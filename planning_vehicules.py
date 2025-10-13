import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from io import BytesIO
import json
import os
import copy
import re  # Pour les expressions régulières

# Configuration de la page
st.set_page_config(page_title="TestDrive Planner App", layout="wide")
st.title("🧠🚗 TestDrive Planner App avec GenAI")

# Dossier de sauvegarde des projets
DOSSIER_PROJETS = "projets_vehicules"
os.makedirs(DOSSIER_PROJETS, exist_ok=True)

# Sidebar pour le prompt utilisateur
st.sidebar.subheader("🧠 Générer un planning avec GenAI")
prompt_global = st.sidebar.text_area("Décris ton besoin global")

# Fonction pour extraire les dates du prompt
def extraire_dates(prompt):
    date_patterns = [
        r'\b(\d{1,2}/\d{1,2}/\d{4})\b',
        r'\b(le\s+)?(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\b'
    ]
    dates = []
    for pattern in date_patterns:
        matches = re.findall(pattern, prompt, re.IGNORECASE)
        for match in matches:
            try:
                if '/' in match[0]:
                    dates.append(datetime.strptime(match[0], "%d/%m/%Y").date())
                else:
                    jour = int(match[1])
                    mois = match[2].lower()
                    mois_num = {
                        "janvier": 1, "février": 2, "mars": 3, "avril": 4, "mai": 5,
                        "juin": 6, "juillet": 7, "août": 8, "septembre": 9,
                        "octobre": 10, "novembre": 11, "décembre": 12
                    }[mois]
                    dates.append(datetime(datetime.today().year, mois_num, jour).date())
            except:
                continue
    return dates

# Génération du planning à partir du prompt
def generer_planning_depuis_prompt(prompt):
    if not prompt.strip():
        return []

    dates_extraites = extraire_dates(prompt)
    start_date = dates_extraites[0] if dates_extraites else datetime.today().date() + timedelta(days=1)

    nb_vehicules = 4 if "3" in prompt else 2
    interlocuteurs = [n for n in ["Alice", "Bob"] if n in prompt]
    if not interlocuteurs:
        interlocuteurs = ["Alice", "Bob"]
    types_essais = [t for t in ["Freinage", "Thermique"] if t.lower() in prompt.lower()]
    if not types_essais:
        types_essais = ["Freinage", "Thermique"]
    durees = [2, 3, 4]

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

# Génération des véhicules si prompt fourni
vehicules = generer_planning_depuis_prompt(prompt_global) if prompt_global else []

# Bouton pour générer le planning
if st.sidebar.button("📅 Générer le planning"):
    planning = []
    for veh in vehicules:
        for test in veh["essais"]:
            if test["nom"] and test["interlocuteur"] and test["date_debut"] and int(test["duree"]) > 0:
                date_debut = pd.to_datetime(test["date_debut"]).date()
                date_fin = pd.to_datetime(test["date_fin"]).date()
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
        fig = px.timeline(df, x_start="Date Début", x_end="Date Fin", y="ID Véhicule", color="Nom du Test",
                          hover_data=["Interlocuteur", "Durée (jours)", "Semaine"])
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📤 Export Excel")
        def convert_df_to_excel(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Planning')
            return output.getvalue()

        excel_data = convert_df_to_excel(df)
        st.download_button("📥 Télécharger le planning Excel", data=excel_data,
                           file_name="planning_genai.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.warning("⚠️ Aucun essai valide pour générer le planning.")
