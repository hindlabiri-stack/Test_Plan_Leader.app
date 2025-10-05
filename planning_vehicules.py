import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from io import BytesIO
import os
import json

# Configuration de la page
st.set_page_config(page_title="Planification des essais véhicules", layout="wide")
st.title("🚗 Planification des essais des véhicules")

# 📁 Gestion des projets
st.sidebar.header("📁 Gestion des projets")
mode_projet = st.sidebar.radio("Mode", ["Créer un nouveau projet", "Charger un projet existant"])
nom_projet = st.sidebar.text_input("Nom du projet", value="Projet_1")

vehicules = []
essais = []
planning = []

# 📂 Chargement d’un projet existant
if mode_projet == "Charger un projet existant":
    os.makedirs("projets", exist_ok=True)
    projets_disponibles = [f for f in os.listdir("projets") if f.endswith(".json")]
    projet_selectionne = st.sidebar.selectbox("Sélectionner un projet", projets_disponibles)
    if projet_selectionne:
        with open(f"projets/{projet_selectionne}", "r") as f:
            data = json.load(f)
            vehicules = data["vehicules"]
            essais = data["essais"]
            planning = data.get("planning", [])
        st.sidebar.success(f"Projet '{projet_selectionne}' chargé.")
else:
    # 📋 Données des véhicules
    st.sidebar.header("📋 Données des véhicules")
    nb_vehicules = st.sidebar.number_input("Nombre de véhicules", min_value=1, max_value=20, value=2)
    for i in range(nb_vehicules):
        st.sidebar.subheader(f"Véhicule {i+1}")
        id_veh = st.sidebar.text_input(f"ID Véhicule {i+1}", value=f"V{i+1:03}")
        sopm = st.sidebar.date_input(f"Date SOPM {id_veh}", key=f"sopm_{i}")
        lrm = st.sidebar.date_input(f"Date LRM {id_veh}", key=f"lrm_{i}")
        vehicules.append({"id": id_veh, "sopm": sopm.isoformat(), "lrm": lrm.isoformat()})

 st.sidebar.header("🧪 Définition des essais")
essais = []
nb_essais = st.sidebar.number_input("Nombre de types d'essais", min_value=1, max_value=10, value=3)

for j in range(nb_essais):
    nom_test = st.sidebar.text_input(f"Nom du test {j+1}", value=f"Test {j+1}")
    interlocuteur = st.sidebar.text_input(f"Interlocuteur du test {nom_test}", value=f"Interlocuteur {j+1}")
    duree = st.sidebar.number_input(f"Durée (jours) du test {nom_test}", min_value=1, max_value=30, value=2, key=f"duree_{j}")
    date_debut_test = st.sidebar.date_input(f"Date début du test {nom_test}", key=f"date_debut_{j}")
    
    essais.append({
        "nom": nom_test,
        "duree": duree,
        "interlocuteur": interlocuteur,
        "date_debut": date_debut_test
    })
        

# 💾 Sauvegarde du projet
def sauvegarder_projet(nom, vehicules, essais, planning):
    os.makedirs("projets", exist_ok=True)
    with open(f"projets/{nom}.json", "w") as f:
        json.dump({"vehicules": vehicules, "essais": essais, "planning": planning}, f, default=str)

# 📅 Génération du planning
if st.button("📅 Générer le planning"):
    planning = []
    today = datetime.today().date()
    for veh in vehicules:
        date_courante = datetime.strptime(veh["sopm"], "%Y-%m-%d").date()
        for test in essais:
            date_debut = date_courante
            date_fin = date_debut + timedelta(days=test["duree"] - 1)
            semaine = date_debut.isocalendar()[1]
            sopm_date = datetime.strptime(veh["sopm"], "%Y-%m-%d").date()
            lrm_date = datetime.strptime(veh["lrm"], "%Y-%m-%d").date()
            alerte_sopm = "⚠️" if (sopm_date - today).days <= 3 else ""
            alerte_lrm = "⚠️" if (lrm_date - today).days <= 3 else ""
            alerte_fin_test = "🔔" if (date_fin - today).days <= 2 else ""
            planning.append({
                "ID Véhicule": veh["id"],
                "Nom du Test": test["nom"],
                "Interlocuteur": test["interlocuteur"],
                "Date Début": date_debut,
                "Date Fin": date_fin,
                "Durée (jours)": test["duree"],
                "Semaine": semaine,
                "Date SOPM": f"{veh['sopm']} {alerte_sopm}",
                "Date LRM": f"{veh['lrm']} {alerte_lrm}",
                "Alerte Fin Test": alerte_fin_test
            })
            date_courante = date_fin + timedelta(days=1)

    df = pd.DataFrame(planning)
    st.success("✅ Planning généré avec succès !")
    sauvegarder_projet(nom_projet, description_projet, vehicules, essais)
    st.success(f"💾 Projet '{nom_projet}' sauvegardé avec succès !")

    st.subheader("📄 Tableau du planning")
    st.dataframe(df)

    st.subheader("📊 Visualisation Gantt")
    fig = px.timeline(
        df,
        x_start="Date Début",
        x_end="Date Fin",
        y="ID Véhicule",
        color="Nom du Test",
        hover_data=["Nom du Test", "Interlocuteur", "Durée (jours)", "Semaine", "Date SOPM", "Date LRM"]
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(title="Planning des essais par véhicule", xaxis_title="Date", yaxis_title="Véhicule")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📥 Exporter le tableau Excel")
    def convert_df_to_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Planning')
        return output.getvalue()

    excel_data = convert_df_to_excel(df)
    st.download_button(
        label="📥 Télécharger le fichier Excel",
        data=excel_data,
        file_name="planning_essais_vehicules.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    df = pd.DataFrame(planning)
    sauvegarder_projet(nom_projet, vehicules, essais, planning)
    st.success(f"✅ Planning généré et projet '{nom_projet}' enregistré avec succès !")

    # 📊 Tableau du planning
    st.subheader("📊 Tableau du planning")
    st.dataframe(df)

    # 📈 Visualisation Gantt
    st.subheader("📈 Visualisation Gantt")
    fig = px.timeline(
        df,
        x_start="Date Début",
        x_end="Date Fin",
        y="ID Véhicule",
        color="Nom du Test",
        hover_data=["Nom du Test", "Interlocuteur", "Durée (jours)", "Semaine", "Date SOPM", "Date LRM"]
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(title="Planning des essais par véhicule", xaxis_title="Date", yaxis_title="Véhicule")
    st.plotly_chart(fig, use_container_width=True)

    # 📥 Export Excel
    st.subheader("📥 Exporter le tableau Excel")
    def convert_df_to_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Planning')
        return output.getvalue()

    excel_data = convert_df_to_excel(df)
    st.download_button(
        label="📥 Télécharger le fichier Excel",
        data=excel_data,
        file_name="planning_essais_vehicules.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
