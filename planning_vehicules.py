import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from io import BytesIO
import json
import os
import copy

st.set_page_config(page_title="TestDrive Planner App", layout="wide")
st.title("🧠🚗 TestDrive Planner App avec GenAI")

DOSSIER_PROJETS = "projets_vehicules"
FICHIER_DERNIER_PROJET = "dernier_projet.json"
os.makedirs(DOSSIER_PROJETS, exist_ok=True)

def sauvegarder_dernier_projet(nom):
    with open(FICHIER_DERNIER_PROJET, "w") as f:
        json.dump({"nom": nom}, f)

def charger_dernier_projet():
    if os.path.exists(FICHIER_DERNIER_PROJET):
        with open(FICHIER_DERNIER_PROJET, "r") as f:
            return json.load(f).get("nom", "")
    return ""

# 🧠 Zone GenAI
st.sidebar.subheader("🧠 Générer un planning avec GenAI")
prompt_global = st.sidebar.text_area("Décris ton besoin global (ex: 3 véhicules, essais de freinage et thermique, sur 2 semaines, Alice et Bob)")

def generer_planning_depuis_prompt(prompt):
    if not prompt.strip():
        return []

    nb_vehicules = 4 if "3" in prompt else 2
    interlocuteurs = []
    if "Alice" in prompt:
        interlocuteurs.append("Alice")
    if "Bob" in prompt:
        interlocuteurs.append("Bob")
    if not interlocuteurs:
        interlocuteurs = ["Alice", "Bob"]

    types_essais = []
    if "freinage" in prompt:
        types_essais.append("Freinage")
    if "thermique" in prompt:
        types_essais.append("Thermique")
    if not types_essais:
        types_essais = ["Freinage", "Thermique"]

    durees = [2, 3, 4]
    start_date = datetime.today().date() + timedelta(days=1)

    vehicules = []
    for i in range(nb_vehicules):
        essais = []
        current_date = start_date
        for essai_type in types_essais:
            interlocuteur = interlocuteurs[i % len(interlocuteurs)]
            duree = durees[(i + len(essais)) % len(durees)]
            date_debut = current_date
            date_fin = current_date + timedelta(days=duree)
            essais.append({
                "nom": f"Essai {essai_type}",
                "interlocuteur": interlocuteur,
                "duree": duree,
                "date_debut": str(date_debut),
                "date_fin": str(date_fin)
            })
            current_date = date_fin + timedelta(days=1)

        vehicules.append({
            "id": f"V{i+1:03}",
            "sopm": str(start_date),
            "lrm": str(start_date + timedelta(days=14)),
            "essais": essais
        })

    return vehicules

# 📦 Chargement des projets
projets_existants = [f.replace(".json", "") for f in os.listdir(DOSSIER_PROJETS) if f.endswith(".json")]
dernier_projet = charger_dernier_projet()
projet_selectionne = st.sidebar.selectbox("📂 Charger un projet existant", [""] + projets_existants, index=([""] + projets_existants).index(dernier_projet) if dernier_projet in projets_existants else 0)
nom_projet = st.sidebar.text_input("📝 Nom du projet", value=projet_selectionne if projet_selectionne else "Projet_Test")

vehicules = []
if projet_selectionne:
    with open(os.path.join(DOSSIER_PROJETS, f"{projet_selectionne}.json"), "r") as f:
        data = json.load(f)
        vehicules = copy.deepcopy(data["vehicules"])

# 📦 Génération automatique via GenAI
if prompt_global:
    vehicules_genai = generer_planning_depuis_prompt(prompt_global)
    st.sidebar.success(f"✅ {len(vehicules_genai)} véhicules générés avec essais répartis !")
    vehicules = vehicules_genai

# 🚗 Formulaire véhicules
nb_vehicules = st.sidebar.number_input("Nombre de véhicules", min_value=1, max_value=20, value=len(vehicules) if vehicules else 2)
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
    id_veh = st.sidebar.text_input(f"ID Véhicule {i+1}", value=veh_data["id"], key=f"id_veh_{key_prefix}")
    sopm = st.sidebar.date_input(f"Date SOPM {id_veh}", value=pd.to_datetime(veh_data["sopm"]).date(), key=f"sopm_{key_prefix}")
    lrm = st.sidebar.date_input(f"Date LRM {id_veh}", value=pd.to_datetime(veh_data["lrm"]).date(), key=f"lrm_{key_prefix}")
    nb_essais = st.sidebar.number_input(f"Nombre d'essais pour {id_veh}", min_value=1, max_value=10, value=len(veh_data["essais"]) if veh_data["essais"] else 2, key=f"nb_essais_{key_prefix}")
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
        nom_test = st.sidebar.text_input(f"Nom du test {j+1} ({id_veh})", value=essai_data["nom"], key=f"nom_test_{essai_key_prefix}")
        interlocuteur = st.sidebar.text_input(f"Interlocuteur du test {nom_test} ({id_veh})", value=essai_data["interlocuteur"], key=f"interlocuteur_{essai_key_prefix}")
        duree = st.sidebar.number_input(f"Durée (jours) du test {nom_test} ({id_veh})", min_value=1, max_value=300, value=int(essai_data["duree"]), key=f"duree_{essai_key_prefix}")
        date_debut = st.sidebar.date_input(f"Date de début du test {nom_test} ({id_veh})", value=pd.to_datetime(essai_data["date_debut"]).date(), key=f"date_debut_{essai_key_prefix}")
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

# 💾 Sauvegarde
projet_existe = nom_projet in projets_existants
if projet_existe:
    st.sidebar.warning(f"⚠️ Le projet '{nom_projet}' existe déjà.")
    confirmer_ecrasement = st.sidebar.checkbox("✅ Écraser le projet existant")

if st.sidebar.button("💾 Sauvegarder le projet"):
    if not projet_existe or confirmer_ecrasement:
        with open(os.path.join(DOSSIER_PROJETS, f"{nom_projet}.json"), "w") as f:
            json.dump({"vehicules": vehicules_input}, f, indent=2)
        sauvegarder_dernier_projet(nom_projet)
        st.sidebar.success(f"Projet '{nom_projet}' sauvegardé avec succès ✅")
    else:
        st.sidebar.error("❌ Le projet existe déjà. Cochez la case pour confirmer l’écrasement.")
