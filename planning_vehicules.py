import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import random

# ⚙️ Configuration de la page
st.set_page_config(page_title="TestDrive Planner avec GenAI", layout="wide")
st.title("🚗🧠 TestDrive Planner avec GenAI pour la planification intelligente des essais")

# 🧠 Zone GenAI : Suggestions intelligentes
st.sidebar.subheader("🧠 Suggestion automatique par GenAI")
prompt = st.sidebar.text_area("Décris le type d'essai ou le besoin (ex: test de freinage sur route humide)")

# Fonction simulée de génération GenAI
# Dans un vrai environnement, on utiliserait un modèle comme GPT ou Claude
def generer_suggestions(prompt):
    if not prompt.strip():
        return "", "", 2, str(datetime.today().date())

    nom_test = f"Essai: {prompt[:30]}..."
    interlocuteur = random.choice(["Alice", "Bob", "Claire", "David"])
    duree = random.choice([1, 2, 3, 5])
    date_debut = str(datetime.today().date() + timedelta(days=random.randint(1, 10)))
    return nom_test, interlocuteur, duree, date_debut

# Affichage des suggestions
if prompt:
    nom_test, interlocuteur, duree, date_debut = generer_suggestions(prompt)
    st.sidebar.markdown("### 💡 Suggestions GenAI")
    st.sidebar.write(f"**Nom du test suggéré :** {nom_test}")
    st.sidebar.write(f"**Interlocuteur suggéré :** {interlocuteur}")
    st.sidebar.write(f"**Durée suggérée :** {duree} jours")
    st.sidebar.write(f"**Date de début suggérée :** {date_debut}")
else:
    st.sidebar.info("Saisis une description pour obtenir des suggestions intelligentes.")
