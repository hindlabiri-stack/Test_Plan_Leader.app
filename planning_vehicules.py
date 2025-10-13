import streamlit as st
import random
from datetime import datetime, timedelta

# 🧠 Génération automatique d'un planning à partir d'un prompt global
st.sidebar.subheader("🧠 Générer un planning complet avec GenAI")
prompt_global = st.sidebar.text_area("Décris ton besoin global (ex: 3 véhicules, essais de freinage et thermique, sur 2 semaines, Alice et Bob)")

# Fonction simulée de génération de planning
def generer_planning_depuis_prompt(prompt):
    if not prompt.strip():
        return []

    # Simulation : extraire nombre de véhicules et interlocuteurs
    nb_vehicules = 3 if "3" in prompt else 2
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
            interlocuteur = random.choice(interlocuteurs)
            duree = random.choice(durees)
            essais.append({
                "nom": f"Essai {essai_type}",
                "interlocuteur": interlocuteur,
                "duree": duree,
                "date_debut": str(current_date)
            })
            current_date += timedelta(days=duree + 1)

        vehicules.append({
            "id": f"V{i+1:03}",
            "sopm": str(start_date),
            "lrm": str(start_date + timedelta(days=14)),
            "essais": essais
        })

    return vehicules

# Affichage du planning généré
if prompt_global:
    vehicules_genai = generer_planning_depuis_prompt(prompt_global)
    st.sidebar.success(f"✅ {len(vehicules_genai)} véhicules générés avec essais répartis !")
    for veh in vehicules_genai:
        st.sidebar.markdown(f"### 🚗 {veh['id']}")
        for essai in veh["essais"]:
            st.sidebar.write(f"- {essai['nom']} ({essai['interlocuteur']}) du {essai['date_debut']} pendant {essai['duree']} jours")
