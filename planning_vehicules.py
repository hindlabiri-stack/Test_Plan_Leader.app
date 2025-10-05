import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from io import BytesIO
import json
import os
import copy

st.set_page_config(page_title="Planification des essais véhicules", layout="wide")
st.title("🚗 Planification des essais des véhicules")

# 📁 Dossiers et fichiers
DOSSIER_PROJETS = "projets_vehicules"
FICHIER_DERNIER_PROJET = "dernier_projet.json"
os.makedirs(DOSSIER_PROJETS, exist_ok=True)

# 🔧 Fonctions de persistance
def sauvegarder_dernier_projet(nom):
    with open(FICHIER_DERNIER_PROJET, "w") as f:
        json.dump({"nom": nom}, f)

def charger_dernier_projet():
    if os.path.exists(FICHIER_DERNIER_PROJET):
        with open(FICHIER_DERNIER_PROJET, "r") as f:
            return json.load(f).get("nom", "")
    return ""

# 📂 Chargement des projets existants
projets_existants = [f.replace(".json", "") for f in os.listdir(DOSSIER_PROJETS) if f.endswith(".json")]
dernier_projet = charger_dernier_projet()
projet_selectionne = st.sidebar.selectbox(
    "📂 Charger un projet existant",
    [""] + projets_existants,
    index=([""] + projets_existants).index(dernier_projet) if dernier_projet in projets_existants else 0
)

# 📝 Nom du projet actuel
nom_projet = st.sidebar.text_input("📝 Nom du projet", value=projet_selectionne if projet_selectionne else "Projet_Test")

# 🔄 Chargement du projet sélectionné (copie profonde)
vehicules = []
if projet_selectionne:
    with open(os.path.join(DOSSIER_PROJETS, f"{projet_selectionne}.json"), "r") as f:
        data = json.load(f)
    vehicules = copy.deepcopy(data["vehicules"])

# 🧮 Nombre de véhicules
nb_vehicules = st.sidebar.number_input(
    "Nombre de véhicules", min_value=1, max_value=20,
    value=len(vehicules) if vehicules else 2,
    key=f"nb_vehicules_{nom_projet}"
)

# 🏁 Construction des données véhicules
vehicules_input = []
for i in range(nb_vehicules):
    st.sidebar.subheader(f"Véhicule {i+1}")
    if i < len(vehicules):
        veh_data = copy.deepcopy(vehicules[i])
    else:
        veh_data = {
            "id": f"V{i+1:03}",
            "sopm": str(datetime.today().date()),
            "lrm": str(datetime.today().date()),
            "essais": []
        }

    key_prefix = f"{nom_projet}_{i}"
    id_veh = st.sidebar.text_input(
        f"ID Véhicule {i+1}", value=veh_data["id"], key=f"id_veh_{key_prefix}"
    )
    sopm = st.sidebar.date_input(
        f"Date SOPM {id_veh}", value=pd.to_datetime(veh_data["sopm"]).date(), key=f"sopm_{key_prefix}"
    )
    lrm = st.sidebar.date_input(
        f"Date LRM {id_veh}", value=pd.to_datetime(veh_data["lrm"]).date(), key=f"lrm_{key_prefix}"
    )

    nb_essais = st.sidebar.number_input(
        f"Nombre d'essais pour {id_veh}", min_value=1, max_value=10,
        value=len(veh_data["essais"]) if veh_data["essais"] else 2,
        key=f"nb_essais_{key_prefix}"
    )

    essais = []
    for j in range(nb_essais):
        if j < len(veh_data["essais"]):
            essai_data = copy.deepcopy(veh_data["essais"][j])
        else:
            essai_data = {
                "nom": f"Test {j+1}",
                "interlocuteur": f"Interlocuteur {j+1}",
                "duree": 2,
                "date_debut": str(datetime.today().date())
            }

        essai_key_prefix = f"{nom_projet}_{i}_{j}"
        nom_test = st.sidebar.text_input(
            f"Nom du test {j+1} ({id_veh})", value=essai_data["nom"], key=f"nom_test_{essai_key_prefix}"
        )
        interlocuteur = st.sidebar.text_input(
            f"Interlocuteur du test {nom_test} ({id_veh})", value=essai_data["interlocuteur"], key=f"interlocuteur_{essai_key_prefix}"
        )
        duree = st.sidebar.number_input(
            f"Durée (jours) du test {nom_test} ({id_veh})", min_value=1, max_value=30,
            value=int(essai_data["duree"]), key=f"duree_{essai_key_prefix}"
        )
        date_debut = st.sidebar.date_input(
            f"Date de début du test {nom_test} ({id_veh})", value=pd.to_datetime(essai_data["date_debut"]).date(),
            key=f"date_debut_{essai_key_prefix}"
        )

        essais.append({
            "nom": nom_test,
            "interlocuteur": interlocuteur,
            "duree": duree,
            "date_debut": str(date_debut)
        })

    vehicules_input.append({
        "id": id_veh,
        "sopm": str(sopm),
        "lrm": str(lrm),
        "essais": essais
    })
