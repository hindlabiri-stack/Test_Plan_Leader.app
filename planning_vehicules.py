import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from io import BytesIO
import json
import os
import copy

st.set_page_config(page_title="Management et Planification des Essais véhicules pour ITPL & VPM", layout="wide")
st.title("🧑‍🔧👩‍🔧🛠️🚗 Management et Planification des Essais véhicules pour ITPL & VPM")

# 📁 Dossiers et fichiers
DOSSIER_PROJETS = "projets_vehicules"
FICHIER_DERNIER_PROJET = "dernier_projet.json"
os.makedirs(DOSSIER_PROJETS, exist_ok=True)

# 🔧 Fonctions de persistance
def sauvegarder_dernier_projet(nom):
    with open(FICHIER_DERNIER_PROJET, "w") as f:
        json.dump({"nom": nom}, f)

def charger_dernier_projet():
    if os.path.exists(FICHIER_DERNIER_PROJET):
        with open(FICHIER_DERNIER_PROJET, "r") as f:
            return json.load(f).get("nom", "")
    return ""

# 📂 Chargement des projets existants
projets_existants = [f.replace(".json", "") for f in os.listdir(DOSSIER_PROJETS) if f.endswith(".json")]
dernier_projet = charger_dernier_projet()
projet_selectionne = st.sidebar.selectbox(
    "📂 Charger un projet existant",
    [""] + projets_existants,
    index=([""] + projets_existants).index(dernier_projet) if dernier_projet in projets_existants else 0
)

# 📝 Nom du projet actuel
nom_projet = st.sidebar.text_input("📝 Nom du projet", value=projet_selectionne if projet_selectionne else "Projet_Test")

# 🔄 Chargement du projet sélectionné (copie profonde)
vehicules = []
if projet_selectionne:
    with open(os.path.join(DOSSIER_PROJETS, f"{projet_selectionne}.json"), "r") as f:
        data = json.load(f)
    vehicules = copy.deepcopy(data["vehicules"])

# 🧮 Nombre de véhicules
nb_vehicules = st.sidebar.number_input(
    "Nombre de véhicules", min_value=1, max_value=20,
    value=len(vehicules) if vehicules else 2,
    key=f"nb_vehicules_{nom_projet}"
)

# 🏁 Construction des données véhicules
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
    id_veh = st.sidebar.text_input(
        f"ID Véhicule {i+1}", value=veh_data["id"], key=f"id_veh_{key_prefix}"
    )
    sopm = st.sidebar.date_input(
        f"Date SOPM {id_veh}", value=pd.to_datetime(veh_data["sopm"]).date(), key=f"sopm_{key_prefix}"
    )
    lrm = st.sidebar.date_input(
        f"Date LRM {id_veh}", value=pd.to_datetime(veh_data["lrm"]).date(), key=f"lrm_{key_prefix}"
    )

    nb_essais = st.sidebar.number_input(
        f"Nombre d'essais pour {id_veh}", min_value=1, max_value=10,
        value=len(veh_data["essais"]) if veh_data["essais"] else 2,
        key=f"nb_essais_{key_prefix}"
    )

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
        nom_test = st.sidebar.text_input(
            f"Nom du test {j+1} ({id_veh})", value=essai_data["nom"], key=f"nom_test_{essai_key_prefix}"
        )
        interlocuteur = st.sidebar.text_input(
            f"Interlocuteur du test {nom_test} ({id_veh})", value=essai_data["interlocuteur"], key=f"interlocuteur_{essai_key_prefix}"
        )
        duree = st.sidebar.number_input(
            f"Durée (jours) du test {nom_test} ({id_veh})", min_value=1, max_value=30,
            value=int(essai_data["duree"]), key=f"duree_{essai_key_prefix}"
        )
        date_debut = st.sidebar.date_input(
            f"Date de début du test {nom_test} ({id_veh})", value=pd.to_datetime(essai_data["date_debut"]).date(),
            key=f"date_debut_{essai_key_prefix}"
        )

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

# 🔐 Vérification avant sauvegarde
projet_existe = nom_projet in projets_existants
if projet_existe:
    st.sidebar.warning(f"⚠️ Le projet '{nom_projet}' existe déjà.")
    confirmer_ecrasement = st.sidebar.checkbox("✅ Écraser le projet existant")

# 💾 Sauvegarde du projet
if st.sidebar.button("💾 Sauvegarder le projet"):
    if not projet_existe or confirmer_ecrasement:
        with open(os.path.join(DOSSIER_PROJETS, f"{nom_projet}.json"), "w") as f:
            json.dump({"vehicules": vehicules_input}, f, indent=2)
        sauvegarder_dernier_projet(nom_projet)
        st.sidebar.success(f"Projet '{nom_projet}' sauvegardé avec succès ✅")
    else:
        st.sidebar.error("❌ Le projet existe déjà. Cochez la case pour confirmer l’écrasement.")

# ⚠️ Détection des chevauchements
chevauchements = []
for veh in vehicules_input:
    essais = veh["essais"]
    for i in range(len(essais)):
        debut_i = pd.to_datetime(essais[i]["date_debut"]).date()
        fin_i = debut_i + timedelta(days=int(essais[i]["duree"]) - 1)
        for j in range(i + 1, len(essais)):
            debut_j = pd.to_datetime(essais[j]["date_debut"]).date()
            fin_j = debut_j + timedelta(days=int(essais[j]["duree"]) - 1)
            if debut_i <= fin_j and debut_j <= fin_i:
                chevauchements.append({
                    "ID Véhicule": veh["id"],
                    "Test 1": essais[i]["nom"],
                    "Test 2": essais[j]["nom"],
                    "Dates Test 1": f"{debut_i} → {fin_i}",
                    "Dates Test 2": f"{debut_j} → {fin_j}"
                })

if chevauchements:
    st.warning("⚠️ Des chevauchements ont été détectés entre les essais !")
    st.write(pd.DataFrame(chevauchements))

# 📅 Génération du planning
if st.button("📅 Générer le planning"):
    planning = []
    today = datetime.today().date()
    for veh in vehicules_input:
        for test in veh["essais"]:
            if test["nom"] and test["interlocuteur"] and test["date_debut"] and int(test["duree"]) > 0:
                date_debut = pd.to_datetime(test["date_debut"]).date()
                date_fin = date_debut + timedelta(days=int(test["duree"]) - 1)
                semaine = date_debut.isocalendar()[1]
                sopm = pd.to_datetime(veh["sopm"]).date()
                lrm = pd.to_datetime(veh["lrm"]).date()
                alerte_sopm = "⚠️" if (sopm - today).days <= 3 else ""
                alerte_lrm = "⚠️" if (lrm - today).days <= 3 else ""
                alerte_fin_test = "🔔" if (date_fin - today).days <= 2 else ""
                planning.append({
                    "ID Véhicule": veh["id"],
                    "Nom du Test": test["nom"],
                    "Interlocuteur": test["interlocuteur"],
                    "Date Début": date_debut,
                    "Date Fin": date_fin,
                    "Durée (jours)": test["duree"],
                    "Semaine": semaine,
                    "Date SOPM": f"{sopm} {alerte_sopm}",
                    "Date LRM": f"{lrm} {alerte_lrm}",
                    "Alerte Fin Test": alerte_fin_test
                })

    if planning:
        df = pd.DataFrame(planning)
        st.success("✅ Planning généré avec succès !")

        st.subheader("📄 Tableau du planning")
        st.dataframe(df)

        st.subheader("📊 Visualisation Gantt")
        fig = px.timeline(
            df,
            x_start="Date Début",
            x_end="Date Fin",
            y="ID Véhicule",
            color="Nom du Test",
            hover_data=["Nom du Test", "Interlocuteur", "Durée (jours)", "Semaine", "Date SOPM", "Date LRM"]
        )
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(title="Planning des essais par véhicule", xaxis_title="Date", yaxis_title="Véhicule")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📥 Exporter le tableau Excel")
        def convert_df_to_excel(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Planning')
            return output.getvalue()

        excel_data = convert_df_to_excel(df)
        st.download_button(
            label="📥 Télécharger le fichier Excel",
            data=excel_data,
            file_name=f"{nom_projet}_planning.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("⚠️ Aucun essai défini correctement pour générer le planning.")
