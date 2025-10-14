import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from io import BytesIO
from openai import OpenAI
import os
import json

# Configuration Streamlit
st.set_page_config(page_title="TestDrive Planner GenAI", layout="wide")
st.title("🤖🚗 TestDrive Planner avec IA Générative")

# Initialisation du client OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Zone de saisie pour le prompt libre
prompt_global = st.sidebar.text_area("Décris ton besoin (ex: 'Planifie 2 véhicules avec NVH en novembre')")

def generer_planning_ia(prompt):
    system_msg = """
    Tu es un assistant qui génère un planning structuré pour des essais véhicules.
    Retourne un JSON avec ce format :
    [
      {
        "id": "V001",
        "interlocuteur": "Alice",
        "essais": [
          {"nom": "NVH", "date_debut": "2025-11-01", "date_fin": "2025-11-05"},
          {"nom": "Climatique", "date_debut": "2025-11-10", "date_fin": "2025-11-15"}
        ]
      }
    ]
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    return response.choices[0].message.content

# Bouton pour générer via IA
if st.sidebar.button("🤖 Générer via IA"):
    planning_json = generer_planning_ia(prompt_global)
    st.subheader("📦 Données générées par IA")
    st.code(planning_json, language="json")

    # Conversion en DataFrame
    try:
        planning_data = json.loads(planning_json)
        rows = []
        for veh in planning_data:
            for essai in veh["essais"]:
                date_debut = pd.to_datetime(essai["date_debut"]).date()
                date_fin = pd.to_datetime(essai["date_fin"]).date()
                rows.append({
                    "ID Véhicule": veh["id"],
                    "Interlocuteur": veh["interlocuteur"],
                    "Nom du Test": essai["nom"],
                    "Date Début": date_debut,
                    "Date Fin": date_fin,
                    "Durée (jours)": (date_fin - date_debut).days,
                    "Semaine": date_debut.isocalendar()[1]
                })
        df = pd.DataFrame(rows)

        # Affichage tableau
        st.subheader("📋 Tableau du planning")
        st.dataframe(df)

        # Diagramme Gantt
        st.subheader("📊 Diagramme de Gantt")
        fig = px.timeline(df, x_start="Date Début", x_end="Date Fin", y="ID Véhicule", color="Nom du Test",
                          hover_data=["Interlocuteur", "Durée (jours)", "Semaine"])
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)

        # Export Excel
        st.subheader("📤 Export Excel")
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Planning')
        st.download_button("📥 Télécharger le planning Excel", data=output.getvalue(),
                           file_name="planning_genai.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        st.error(f"Erreur lors du parsing du JSON : {e}")
