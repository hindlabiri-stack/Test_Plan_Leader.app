import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from io import BytesIO
import json
import os

# Configuration de la page
st.set_page_config(page_title="Planification des essais véhicules", layout="wide")
st.title("🚗 Planification des essais des véhicules")

# Dossier de sauvegarde des projets
DOSSIER_PROJETS = "projets"
os.makedirs(DOSSIER_PROJETS, exist_ok=True)

# Chargement des projets existants
liste_projets = [f.split(".")[0] for f in os.listdir(DOSSIER_PROJETS) if f.endswith(".json")]
projet_selectionne = st.sidebar.selectbox("📂 Sélectionner un projet existant", options=[""] + liste_projets)

# Initialisation des variables
nom_projet = ""
description_projet = ""
vehicules = []
essais = []

# Chargement du projet sélectionné
if projet_selectionne:
    with open(f"{DOSSIER_PROJETS}/{projet_selectionne}.json", "r", encoding="utf-8") as f:
        projet_charge = json.load(f)
    nom_projet = projet_charge["nom"]
    description_projet = projet_charge["description"]
    vehicules = projet_charge["vehicules"]
    essais = projet_charge["essais"]
    st.sidebar.success(f"✅ Projet '{nom_projet}' chargé avec succès.")

# Modification du nom et de la description
st.sidebar.header("📝 Modifier le projet")
nom_projet = st.sidebar.text_input("Nom du projet", value=nom_projet)
description_projet = st.sidebar.text_area("Description du projet", value=description_projet)

# Modification des véhicules
st.sidebar.header("🚙 Modifier les véhicules")
nb_vehicules = st.sidebar.number_input("Nombre de véhicules", min_value=1, max_value=20, value=len(vehicules) if vehicules else 2)
vehicules_modifies = []
for i in range(nb_vehicules):
    st.sidebar.subheader(f"Véhicule {i+1}")
    id_veh = st.sidebar.text_input(f"ID Véhicule {i+1}", value=vehicules[i]["id"] if i < len(vehicules) else f"V{i+1:03}")
    sopm = st.sidebar.date_input(f"Date SOPM {id_veh}", value=datetime.strptime(vehicules[i]["sopm"], "%Y-%m-%d").date() if i < len(vehicules) else datetime.today().date(), key=f"sopm_{i}")
    lrm = st.sidebar.date_input(f"Date LRM {id_veh}", value=datetime.strptime(vehicules[i]["lrm"], "%Y-%m-%d").date() if i < len(vehicules) else datetime.today().date(), key=f"lrm_{i}")
    vehicules_modifies.append({"id": id_veh, "sopm": str(sopm), "lrm": str(lrm)})

# Modification des essais
st.sidebar.header("🧪 Modifier les essais")
nb_essais = st.sidebar.number_input("Nombre de types d'essais", min_value=1, max_value=10, value=len(essais) if essais else 3)
essais_modifies = []
for j in range(nb_essais):
    nom_test = st.sidebar.text_input(f"Nom du test {j+1}", value=essais[j]["nom"] if j < len(essais) else f"Test {j+1}")
    interlocuteur = st.sidebar.text_input(f"Interlocuteur du test {nom_test}", value=essais[j]["interlocuteur"] if j < len(essais) else f"Interlocuteur {j+1}")
    duree = st.sidebar.number_input(f"Durée (jours) du test {nom_test}", min_value=1, max_value=30, value=essais[j]["duree"] if j < len(essais) else 2, key=f"duree_{j}")
    essais_modifies.append({"nom": nom_test, "duree": duree, "interlocuteur": interlocuteur})

# Fonction de sauvegarde
def sauvegarder_projet(nom, description, vehicules, essais):
    projet = {
        "nom": nom,
        "description": description,
        "vehicules": vehicules,
        "essais": essais
    }
    with open(f"{DOSSIER_PROJETS}/{nom}.json", "w", encoding="utf-8") as f:
        json.dump(projet, f, ensure_ascii=False, indent=4)

# Génération du planning
if st.button("📅 Générer le planning"):
    planning = []
    today = datetime.today().date()
    for veh in vehicules_modifies:
        date_courante = datetime.strptime(veh["sopm"], "%Y-%m-%d").date()
        for test in essais_modifies:
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
    sauvegarder_projet(nom_projet, description_projet, vehicules_modifies, essais_modifies)
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
