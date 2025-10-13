
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

st.sidebar.subheader("🧠 Générer un planning avec GenAI")
prompt_global = st.sidebar.text_area("Décris ton besoin global")

import re
from datetime import datetime, timedelta

def extraire_interlocuteurs(prompt):
    # Recherche tous les mots commençant par une majuscule (supposés être des noms)
    return list(set(re.findall(r'\b[A-Z][a-z]+\b', prompt)))

def extraire_types_essais(prompt):
    # Recherche tous les mots après "essai" ou "test"
    essais = re.findall(r'essai\s+(\w+)', prompt, re.IGNORECASE)
    essais += re.findall(r'test\s+(\w+)', prompt, re.IGNORECASE)
    return list(set(essais)) if essais else ["Freinage", "Thermique"]

def generer_planning_depuis_prompt(prompt):
    if not prompt.strip():
        return []

    nb_vehicules = 4 if "3" in prompt else 2

    interlocuteurs = extraire_interlocuteurs(prompt)
    if not interlocuteurs:
        interlocuteurs = ["Alice", "Bob", "Hind"]

    types_essais = extraire_types_essais(prompt)
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


vehicules = generer_planning_depuis_prompt(prompt_global) if prompt_global else []

if st.sidebar.button("📅 Générer le planning"):
    planning = []
    for veh in vehicules:
        for test in veh["essais"]:
            if test["nom"] and test["interlocuteur"] and test["date_debut"] and int(test["duree"]) > 0:
                date_debut = pd.to_datetime(test["date_debut"]).date()
                date_fin = date_debut + timedelta(days=int(test["duree"]) - 1)
                semaine = date_debut.isocalendar()[1]
                sopm = pd.to_datetime(veh["sopm"]).date()
                lrm = pd.to_datetime(veh["lrm"]).date()
                planning.append({
                    "ID Véhicule": veh["id"],
                    "Nom du Test": test["nom"],
                    "Interlocuteur": test["interlocuteur"],
                    "Date Début": date_debut,
                    "Date Fin": date_fin,
                    "Durée (jours)": test["duree"],
                    "Semaine": semaine,
                    "Date SOPM": sopm,
                    "Date LRM": lrm
                })
    if planning:
        df = pd.DataFrame(planning)
        st.subheader("📋 Tableau du planning")
        st.dataframe(df)

        st.subheader("📊 Diagramme de Gantt")
        fig = px.timeline(df, x_start="Date Début", x_end="Date Fin", y="ID Véhicule", color="Nom du Test", hover_data=["Interlocuteur", "Durée (jours)", "Semaine"])
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📤 Export Excel")
        def convert_df_to_excel(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Planning')
            return output.getvalue()

        excel_data = convert_df_to_excel(df)
        st.download_button("📥 Télécharger le planning Excel", data=excel_data, file_name="planning_genai.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.warning("⚠️ Aucun essai valide pour générer le planning.")
