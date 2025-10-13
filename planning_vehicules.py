import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from io import BytesIO
import re

st.set_page_config(page_title="TestDrive Planner GenAI Libre", layout="wide")
st.title("🧠📅 TestDrive Planner avec saisie libre des essais par véhicule")

st.sidebar.subheader("🧠 Saisie libre du planning")
prompt = st.sidebar.text_area("Décris chaque véhicule et ses essais (exemple ci-dessous)", height=200, value="""
V001: freinage (Alice) du 2025-10-20 au 2025-10-22, thermique (Bob) du 2025-10-24 au 2025-10-26
V002: acoustique (Fatima) du 2025-10-21 au 2025-10-23
V003: endurance (Bob) du 2025-10-25 au 2025-10-28, thermique (Alice) du 2025-10-29 au 2025-10-31, freinage (Bob) du 2025-11-01 au 2025-11-03
""")

vehicules = []

if prompt:
    for ligne in prompt.strip().split("\n"):
        if not ligne.strip():
            continue
        match = re.match(r"(V\\d+):(.+)", ligne)
        if not match:
            continue
        veh_id = match.group(1).strip()
        essais_bruts = match.group(2).split(",")
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
        vehicules.append({
            "id": veh_id,
            "sopm": str(datetime.today().date()),
            "lrm": str(datetime.today().date() + timedelta(days=30)),
            "essais": essais
        })

if st.sidebar.button("📅 Générer le planning"):
    planning = []
    for veh in vehicules:
        for test in veh["essais"]:
            planning.append({
                "ID Véhicule": veh["id"],
                "Nom du Test": test["nom"],
                "Interlocuteur": test["interlocuteur"],
                "Date Début": test["date_debut"],
                "Date Fin": test["date_fin"],
                "Durée (jours)": test["duree"],
                "Date SOPM": veh["sopm"],
                "Date LRM": veh["lrm"]
            })

    if planning:
        df = pd.DataFrame(planning)
        st.subheader("📋 Tableau du planning")
        st.dataframe(df)

        st.subheader("📊 Diagramme de Gantt")
        fig = px.timeline(df, x_start="Date Début", x_end="Date Fin", y="ID Véhicule", color="Nom du Test", hover_data=["Interlocuteur", "Durée (jours)"])
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📤 Export Excel")
        def convert_df_to_excel(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Planning')
            return output.getvalue()

        excel_data = convert_df_to_excel(df)
        st.download_button("📥 Télécharger le planning Excel", data=excel_data, file_name="planning_genai_libre.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.warning("⚠️ Aucun essai valide détecté.")
