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
