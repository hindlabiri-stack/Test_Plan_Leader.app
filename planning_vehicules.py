import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import json
import os

# Configuration de la page
st.set_page_config(page_title="Gestion des projets d'essais véhicules", layout="wide")
st.title("🚗 Gestion des projets d'essais véhicules")

# Dossier de sauvegarde des projets
PROJECTS_DIR = "projets_json"
os.makedirs(PROJECTS_DIR, exist_ok=True)

# Chargement des projets existants
def charger_projets():
    projets = {}
    for fichier in os.listdir(PROJECTS_DIR):
        if fichier.endswith(".json"):
            with open(os.path.join(PROJECTS_DIR, fichier), "r", encoding="utf-8") as f:
                projets[fichier[:-5]] = json.load(f)
    return projets

# Sauvegarde d'un projet
def sauvegarder_projet(nom_projet, data):
    with open(os.path.join(PROJECTS_DIR, f"{nom_projet}.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Interface de sélection ou création de projet
st.sidebar.header("📁 Sélection du projet")
projets_existants = charger_projets()
nom_projet = st.sidebar.selectbox("Choisir un projet existant", [""] + list(projets_existants.keys()))
nouveau_projet = st.sidebar.text_input("Ou créer un nouveau projet", "")

if nouveau_projet:
    nom_projet = nouveau_projet
    projets_existants[nom_projet] = {"vehicules": [], "essais": {}}

if not nom_projet:
    st.warning("Veuillez sélectionner ou créer un projet.")
    st.stop()

# Chargement des données du projet sélectionné
data_projet = projets_existants.get(nom_projet, {"vehicules": [], "essais": {}})
vehicules = data_projet["vehicules"]
essais_par_vehicule = data_projet["essais"]

# Interface pour modifier les véhicules
st.sidebar.header("🚘 Configuration des véhicules")
nb_vehicules = st.sidebar.number_input("Nombre de véhicules", min_value=1, max_value=20, value=len(vehicules) or 1)

vehicules = []
for i in range(nb_vehicules):
    st.sidebar.subheader(f"Véhicule {i+1}")
    id_veh = st.sidebar.text_input(f"Contremarque {i+1}", value=f"V{i+1:03}", key=f"id_{i}")
    vin = st.sidebar.text_input(f"Numéro de VIN {i+1}", value=f"VIN{i+1:05}", key=f"vin_{i}")
    sopm = st.sidebar.date_input(f"Date SOPM {id_veh}", key=f"sopm_{i}")
    vehicules.append({"id": id_veh, "vin": vin, "sopm": str(sopm)})

# Interface pour modifier les essais par véhicule
essais_par_vehicule = {}
st.sidebar.header("🧪 Définition des essais par véhicule")
for veh in vehicules:
    essais = []
    st.sidebar.subheader(f"Essais pour {veh['id']}")
    nb_essais = st.sidebar.number_input(f"Nombre d'essais pour {veh['id']}", min_value=1, max_value=10, value=2, key=f"nb_essais_{veh['id']}")
    for j in range(nb_essais):
        nom_test = st.sidebar.text_input(f"Nom de l'essai {j+1} ({veh['id']})", value=f"Essai {j+1}", key=f"nom_test_{veh['id']}_{j}")
        interlocuteur = st.sidebar.text_input(f"Interlocuteur {nom_test}", value=f"Interlocuteur {j+1}", key=f"interlocuteur_{veh['id']}_{j}")
        duree = st.sidebar.number_input(f"Durée (jours) {nom_test}", min_value=1, max_value=30, value=2, key=f"duree_{veh['id']}_{j}")
        essais.append({"nom": nom_test, "duree": duree, "interlocuteur": interlocuteur})
    essais_par_vehicule[veh["id"]] = essais

# Sauvegarde du projet
if st.sidebar.button("💾 Sauvegarder le projet"):
    sauvegarder_projet(nom_projet, {"vehicules": vehicules, "essais": essais_par_vehicule})
    st.sidebar.success("Projet sauvegardé avec succès.")

# Génération du planning
if st.button("📅 Générer le planning"):
    planning = []
    today = datetime.today().date()
    chevauchements = []

    for veh in vehicules:
        date_courante = datetime.strptime(veh["sopm"], "%Y-%m-%d").date()
        essais = essais_par_vehicule.get(veh["id"], [])
        for idx, test in enumerate(essais):
            date_debut = date_courante
            date_fin = date_debut + timedelta(days=test["duree"] - 1)
            alerte_fin_test = "🔔" if (date_fin - today).days <= 7 else ""
            essai_suivant = essais[idx + 1]["nom"] if idx + 1 < len(essais) else "Aucun"

            for item in planning:
                if item["Contremarque"] == veh["id"]:
                    if not (date_fin < item["Date Début"] or date_debut > item["Date Fin"]):
                        chevauchements.append((veh["id"], test["nom"], item["Nom d'essai"]))

            planning.append({
                "Nom du Projet": nom_projet,
                "Contremarque": veh["id"],
                "Numéro de VIN": veh["vin"],
                "Nom d'essai": test["nom"],
                "Interlocuteur d'essai": test["interlocuteur"],
                "Date Début": date_debut,
                "Date Fin": date_fin,
                "Essai suivant": essai_suivant,
                "Date SOPM": veh["sopm"],
                "Alerte Fin d'essai": alerte_fin_test
            })
            date_courante = date_fin + timedelta(days=1)

    df = pd.DataFrame(planning)
    st.success("✅ Planning généré avec succès !")

    st.subheader("📄 Tableau du planning")
    st.dataframe(df)

    if chevauchements:
        st.warning("⚠️ Chevauchements détectés :")
        for chev in chevauchements:
            st.write(f"Véhicule {chev[0]} : {chev[1]} chevauche avec {chev[2]}")

    st.subheader("📊 Visualisation Gantt")
    fig = px.timeline(
        df, x_start="Date Début", x_end="Date Fin", y="Contremarque", color="Nom d'essai",
        hover_data=["Nom d'essai", "Interlocuteur d'essai", "Essai suivant", "Date SOPM", "Alerte Fin d'essai"]
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(title=f"Planning des essais - {nom_projet}", xaxis_title="Date", yaxis_title="Contremarque")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📥 Exporter le tableau Excel")
    def convert_df_to_excel(df):
        from io import BytesIO
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Planning')
        return output.getvalue()

    excel_data = convert_df_to_excel(df)
    st.download_button(
        label="📥 Télécharger le fichier Excel",
        data=excel_data,
        file_name=f"planning_{nom_projet}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
