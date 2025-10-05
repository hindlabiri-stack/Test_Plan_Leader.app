# 📦 Imports
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from io import BytesIO
import json
import os

# ⚙️ Configuration
st.set_page_config(page_title="Planification des essais véhicules", layout="wide")
st.title("🚗 Planification des essais des véhicules")

# 📁 Gestion des projets
st.sidebar.header("📁 Gestion des projets")
dossier_projets = "projets"
os.makedirs(dossier_projets, exist_ok=True)

# Création ou modification
nom_projet = st.sidebar.text_input("Nom du projet", value="Projet Test")
description_projet = st.sidebar.text_area("Description du projet", value="Description du projet ici...")

# Chargement
liste_projets = [f.split(".")[0] for f in os.listdir(dossier_projets) if f.endswith(".json")]
projet_selectionne = st.sidebar.selectbox("📂 Charger un projet", options=[""] + liste_projets)

vehicules = []
essais = []

if projet_selectionne:
    with open(f"{dossier_projets}/{projet_selectionne}.json", "r", encoding="utf-8") as f:
        projet_charge = json.load(f)
    nom_projet = projet_charge["nom"]
    description_projet = projet_charge["description"]
    vehicules = projet_charge["vehicules"]
    essais = projet_charge["essais"]
    st.sidebar.success(f"📂 Projet '{nom_projet}' chargé")

    # Suppression
    if st.sidebar.button("🗑️ Supprimer ce projet"):
        os.remove(f"{dossier_projets}/{projet_selectionne}.json")
        st.sidebar.warning(f"Projet '{projet_selectionne}' supprimé.")
        st.experimental_rerun()

# 🚙 Données des véhicules
st.sidebar.header("🚙 Données des véhicules")
if not vehicules:
    nb_vehicules = st.sidebar.number_input("Nombre de véhicules", min_value=1, max_value=20, value=2)
    for i in range(nb_vehicules):
        st.sidebar.subheader(f"Véhicule {i+1}")
        id_veh = st.sidebar.text_input(f"ID Véhicule {i+1}", value=f"V{i+1:03}")
        sopm = st.sidebar.date_input(f"Date SOPM {id_veh}", key=f"sopm_{i}")
        lrm = st.sidebar.date_input(f"Date LRM {id_veh}", key=f"lrm_{i}")
        vehicules.append({"id": id_veh, "sopm": str(sopm), "lrm": str(lrm)})

# 🧪 Définition des essais
st.sidebar.header("🧪 Définition des essais")
if not essais:
    nb_essais = st.sidebar.number_input("Nombre de types d'essais", min_value=1, max_value=10, value=3)
    for j in range(nb_essais):
        nom_test = st.sidebar.text_input(f"Nom du test {j+1}", value=f"Test {j+1}")
        interlocuteur = st.sidebar.text_input(f"Interlocuteur du test {nom_test}", value=f"Interlocuteur {j+1}")
        duree = st.sidebar.number_input(f"Durée (jours) du test {nom_test}", min_value=1, max_value=30, value=2, key=f"duree_{j}")
        essais.append({"nom": nom_test, "duree": duree, "interlocuteur": interlocuteur})

# 💾 Sauvegarde
def sauvegarder_projet(nom, description, vehicules, essais):
    projet = {
        "nom": nom,
        "description": description,
        "vehicules": vehicules,
        "essais": essais
    }
    with open(f"{dossier_projets}/{nom}.json", "w", encoding="utf-8") as f:
        json.dump(projet, f, ensure_ascii=False, indent=4)

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

# 🔍 Comparaison de projets
st.sidebar.subheader("🔍 Comparer plusieurs projets")
projets_comparaison = st.sidebar.multiselect("Sélectionner les projets à comparer", options=liste_projets)

if projets_comparaison:
    st.subheader("📊 Comparaison des plannings de projets")
    for nom in projets_comparaison:
        with open(f"{dossier_projets}/{nom}.json", "r", encoding="utf-8") as f:
            projet = json.load(f)
        planning = []
        for veh in projet["vehicules"]:
            date_courante = datetime.strptime(veh["sopm"], "%Y-%m-%d").date()
            for test in projet["essais"]:
                date_debut = date_courante
                date_fin = date_debut + timedelta(days=test["duree"] - 1)
                planning.append({
                    "Projet": nom,
                    "ID Véhicule": veh["id"],
                    "Nom du Test": test["nom"],
                    "Date Début": date_debut,
                    "Date Fin": date_fin
                })
                date_courante = date_fin + timedelta(days=1)
        df_comp = pd.DataFrame(planning)
        fig_comp = px.timeline(
            df_comp,
            x_start="Date Début",
            x_end="Date Fin",
            y="ID Véhicule",
            color="Nom du Test",
            title=f"Planning du projet '{nom}'",
            hover_data=["Projet", "Nom du Test"]
        )
        fig_comp.update_yaxes(autorange="reversed")
        st.plotly_chart(fig_comp, use_container_width=True)
