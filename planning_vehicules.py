import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from io import BytesIO
import os
import re

st.set_page_config(page_title="TestDrive Planner App", layout="wide")
st.title("🧠🚗 TestDrive Planner App avec GenAI")

DOSSIER_PROJETS = "projets_vehicules"
os.makedirs(DOSSIER_PROJETS, exist_ok=True)

st.sidebar.subheader("🧠 Générer un planning avec GenAI")
prompt_global = st.sidebar.text_area("Décris ton besoin global")

# Fonction pour parser un prompt structuré
def parser_prompt_vehicules(prompt):
    vehicules = []

    # Détection du nombre de véhicules
    nb_vehicules_match = re.search(r"je veux (\d+) véhicules", prompt, re.IGNORECASE)
    nb_vehicules = int(nb_vehicules_match.group(1)) if nb_vehicules_match else 0

    # Séparation par véhicule
    vehicule_blocks = re.split(r"le \w+ véhicule concerne", prompt, flags=re.IGNORECASE)[1:]
    interlocuteurs = re.findall(r"le \w+ véhicule concerne ([A-Za-z]+)", prompt, re.IGNORECASE)

    for i, block in enumerate(vehicule_blocks):
        essais = []
        essais_matches = re.findall(
            r"(\w+) du (\d{2}/\d{2}/\d{4}) jusqu(?:'|’)au (\d{2}/\d{2}/\d{4})",
            block,
            re.IGNORECASE
        )
        for nom, debut, fin in essais_matches:
            date_debut = datetime.strptime(debut, "%d/%m/%Y").date()
            date_fin = datetime.strptime(fin, "%d/%m/%Y").date()
            essais.append({
                "nom": nom,
                "interlocuteur": interlocuteurs[i] if i < len(interlocuteurs) else "",
                "duree": (date_fin - date_debut).days,
                "date_debut": str(date_debut),
                "date_fin": str(date_fin)
            })
        vehicules.append({
            "id": f"V{i+1:03}",
            "sopm": essais[0]["date_debut"] if essais else "",
            "lrm": essais[-1]["date_fin"] if essais else "",
            "essais": essais
        })

    return vehicules

# Génération des véhicules à partir du prompt
vehicules = parser_prompt_vehicules(prompt_global) if prompt_global else []

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
