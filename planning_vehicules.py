
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

def generer_planning_depuis_prompt(prompt):
    vehicules = []
    for ligne in prompt.strip().split("\n"):
        if not ligne.strip():
            continue
        match = re.match(r"(V\\d+):\\s*SOPM=(\\d{4}-\\d{2}-\\d{2}),\\s*LRM=(\\d{4}-\\d{2}-\\d{2})\\s*\\|(.*)", ligne)
        if not match:
            st.warning(f"❌ Ligne ignorée (format incorrect) : {ligne}")
            continue
        veh_id = match.group(1).strip()
        sopm = match.group(2).strip()
        lrm = match.group(3).strip()
        essais_bruts = match.group(4).split(",")
        essais = []
        for essai in essais_bruts:
            essai = essai.strip()
            essai_match = re.match(r"(.+?)\\((.+?)\\) du (\\d{4}-\\d{2}-\\d{2}) au (\\d{4}-\\d{2}-\\d{2})", essai)
            if essai_match:
                nom = essai_match.group(1).strip().capitalize()
                interlocuteur = essai_match.group(2).strip()
                date_debut = datetime.strptime(essai_match.group(3), "%Y-%m-%d").date()
                date_fin = datetime.strptime(essai_match.group(4), "%Y-%m-%d").date()
                duree = (date_fin - date_debut).days + 1
                essais.append({
                    "nom": f"Essai {nom}",
                    "interlocuteur": interlocuteur,
                    "date_debut": str(date_debut),
                    "date_fin": str(date_fin),
                    "duree": duree
                })
            else:
                st.warning(f"❌ Essai ignoré (format incorrect) : {essai}")
        vehicules.append({
            "id": veh_id,
            "sopm": sopm,
            "lrm": lrm,
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
