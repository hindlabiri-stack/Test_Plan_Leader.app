import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import json
import os

# Configuration de la page
st.set_page_config(page_title="Gestion des projets d'essais véhicules", layout="wide")
st.title("🚗 Gestion des projets d'essais véhicules")

# Dossier de sauvegarde des projets
PROJECTS_DIR = "projets_json"
os.makedirs(PROJECTS_DIR, exist_ok=True)

# Chargement des projets existants
def charger_projets():
    projets = {}
    for fichier in os.listdir(PROJECTS_DIR):
        if fichier.endswith(".json"):
            with open(os.path.join(PROJECTS_DIR, fichier), "r", encoding="utf-8") as f:
                projets[fichier[:-5]] = json.load(f)
    return projets

# Sauvegarde d'un projet
def sauvegarder_projet(nom_projet, data):
    with open(os.path.join(PROJECTS_DIR, f"{nom_projet}.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Interface de sélection ou création de projet
st.sidebar.header("📁 Projet")
projets_existants = charger_projets()
nom_projet_selectionne = st.sidebar.selectbox("Choisir un projet existant", [""] + list(projets_existants.keys()))
nom_nouveau_projet = st.sidebar.text_input("Ou créer un nouveau projet", "")

# Définir la variable nom_projet correctement
if nom_nouveau_projet:
    nom_projet = nom_nouveau_projet
    data_projet = {"vehicules": [], "essais": {}}
elif nom_projet_selectionne:
    nom_projet = nom_projet_selectionne
    data_projet = projets_existants[nom_projet]
else:
    st.warning("Veuillez sélectionner ou créer un projet.")
    st.stop()

st.subheader(f"📝 Édition du projet : {nom_projet}")

# Interface pour modifier les véhicules
st.markdown("### 🚘 Liste des véhicules")
vehicules = data_projet.get("vehicules", [])
essais_par_vehicule = data_projet.get("essais", {})

vehicules_modifies = []
for i, veh in enumerate(vehicules):
    with st.expander(f"Véhicule {i+1} - {veh['id']}"):
        col1, col2, col3 = st.columns(3)
        id_veh = col1.text_input("Contremarque", value=veh["id"], key=f"id_{i}")
        vin = col2.text_input("Numéro de VIN", value=veh["vin"], key=f"vin_{i}")
        sopm = col3.date_input("Date SOPM", value=datetime.strptime(veh["sopm"], "%Y-%m-%d").date(), key=f"sopm_{i}")
        if st.button(f"🗑️ Supprimer ce véhicule", key=f"supprimer_veh_{i}"):
            continue
        vehicules_modifies.append({"id": id_veh, "vin": vin, "sopm": str(sopm)})

if st.button("➕ Ajouter un véhicule"):
    vehicules_modifies.append({"id": f"V{len(vehicules_modifies)+1:03}", "vin": f"VIN{len(vehicules_modifies)+1:05}", "sopm": str(datetime.today().date())})

vehicules = vehicules_modifies

# Interface pour modifier les essais par véhicule
st.markdown("### 🧪 Essais par véhicule")
essais_par_vehicule_modifies = {}
for veh in vehicules:
    essais = essais_par_vehicule.get(veh["id"], [])
    essais_mod = []
    with st.expander(f"Essais pour {veh['id']}"):
        for j, test in enumerate(essais):
            col1, col2, col3 = st.columns(3)
            nom_test = col1.text_input(f"Nom de l'essai {j+1}", value=test["nom"], key=f"nom_{veh['id']}_{j}")
            interlocuteur = col2.text_input(f"Interlocuteur", value=test["interlocuteur"], key=f"interlocuteur_{veh['id']}_{j}")
            duree = col3.number_input(f"Durée (jours)", min_value=1, max_value=30, value=test["duree"], key=f"duree_{veh['id']}_{j}")
            if st.button(f"🗑️ Supprimer l'essai {j+1}", key=f"supprimer_essai_{veh['id']}_{j}"):
                continue
            essais_mod.append({"nom": nom_test, "interlocuteur": interlocuteur, "duree": duree})
        if st.button(f"➕ Ajouter un essai pour {veh['id']}", key=f"ajouter_essai_{veh['id']}"):
            essais_mod.append({"nom": f"Essai {len(essais_mod)+1}", "interlocuteur": "Interlocuteur", "duree": 2})
    essais_par_vehicule_modifies[veh["id"]] = essais_mod

essais_par_vehicule = essais_par_vehicule_modifies

# Sauvegarde du projet
if st.button("💾 Sauvegarder les modifications"):
    sauvegarder_projet(nom_projet, {"vehicules": vehicules, "essais": essais_par_vehicule})
    st.success("Projet sauvegardé avec succès.")

# Génération du planning
if st.button("📅 Générer le planning"):
    planning = []
    today = datetime.today().date()
    chevauchements = []

    for veh in vehicules:
        date_courante = datetime.strptime(veh["sopm"], "%Y-%m-%d").date()
        essais = essais_par_vehicule.get(veh["id"], [])
        for idx, test in enumerate(essais):
            date_debut = date_courante
            date_fin = date_debut + timedelta(days=test["duree"] - 1)
            alerte_fin_test = "🔔" if (date_fin - today).days <= 7 else ""
            essai_suivant = essais[idx + 1]["nom"] if idx + 1 < len(essais) else "Aucun"

            for item in planning:
                if item["Contremarque"] == veh["id"]:
                    if not (date_fin < item["Date Début"] or date_debut > item["Date Fin"]):
                        chevauchements.append((veh["id"], test["nom"], item["Nom d'essai"]))

            planning.append({
                "Nom du Projet": nom_projet,
                "Contremarque": veh["id"],
                "Numéro de VIN": veh["vin"],
                "Nom d'essai": test["nom"],
                "Interlocuteur d'essai": test["interlocuteur"],
                "Date Début": date_debut,
                "Date Fin": date_fin,
                "Essai suivant": essai_suivant,
                "Date SOPM": veh["sopm"],
                "Alerte Fin d'essai": alerte_fin_test
            })
            date_courante = date_fin + timedelta(days=1)

    df = pd.DataFrame(planning)
    st.success("✅ Planning généré avec succès !")

    st.subheader("📄 Tableau du planning")
    st.dataframe(df)

    if chevauchements:
        st.warning("⚠️ Chevauchements détectés :")
        for chev in chevauchements:
            st.write(f"Véhicule {chev[0]} : {chev[1]} chevauche avec {chev[2]}")

    st.subheader("📊 Visualisation Gantt")
    fig = px.timeline(
        df, x_start="Date Début", x_end="Date Fin", y="Contremarque", color="Nom d'essai",
        hover_data=["Nom d'essai", "Interlocuteur d'essai", "Essai suivant", "Date SOPM", "Alerte Fin d'essai"]
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(title=f"Planning des essais - {nom_projet}", xaxis_title="Date", yaxis_title="Contremarque")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📥 Exporter le tableau Excel")
    def convert_df_to_excel(df):
        from io import BytesIO
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Planning')
        return output.getvalue()

    excel_data = convert_df_to_excel(df)
    st.download_button(
        label="📥 Télécharger le fichier Excel",
        data=excel_data,
        file_name=f"planning_{nom_projet}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
