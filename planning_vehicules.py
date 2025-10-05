import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta, date
from io import BytesIO
import json
import os

st.set_page_config(page_title="Planification des essais véhicules", layout="wide")
st.title("🚗 Planification des essais des véhicules")

# 📁 Dossier de sauvegarde des projets
DOSSIER_PROJETS = "projets_vehicules"
os.makedirs(DOSSIER_PROJETS, exist_ok=True)

# 📂 Chargement des projets existants
projets_existants = [f.replace(".json", "") for f in os.listdir(DOSSIER_PROJETS) if f.endswith(".json")]
projet_selectionne = st.sidebar.selectbox("📂 Charger un projet existant", [""] + projets_existants)

# 📌 Nom du projet actuel
nom_projet = st.sidebar.text_input("📝 Nom du projet", value=projet_selectionne if projet_selectionne else "Projet_Test")

vehicules = []

# 🔄 Chargement du projet sélectionné
if projet_selectionne:
    with open(os.path.join(DOSSIER_PROJETS, f"{projet_selectionne}.json"), "r") as f:
        data = json.load(f)
        vehicules = data["vehicules"]

# 🧮 Nombre de véhicules
nb_vehicules = st.sidebar.number_input("Nombre de véhicules", min_value=1, max_value=20, value=len(vehicules) if vehicules else 2)

for i in range(nb_vehicules):
    st.sidebar.subheader(f"Véhicule {i+1}")
    if i < len(vehicules):
        veh_data = vehicules[i]
    else:
        veh_data = {"id": f"V{i+1:03}", "sopm": str(datetime.today().date()), "lrm": str(datetime.today().date()), "essais": []}

    id_veh = st.sidebar.text_input(f"ID Véhicule {i+1}", value=veh_data["id"], key=f"id_veh_{i}")
    sopm = st.sidebar.date_input(f"Date SOPM {id_veh}", value=pd.to_datetime(veh_data["sopm"]).date(), key=f"sopm_{i}")
    lrm = st.sidebar.date_input(f"Date LRM {id_veh}", value=pd.to_datetime(veh_data["lrm"]).date(), key=f"lrm_{i}")

    nb_essais = st.sidebar.number_input(f"Nombre d'essais pour {id_veh}", min_value=1, max_value=10, value=len(veh_data["essais"]) if veh_data["essais"] else 2, key=f"nb_essais_{i}")
    essais = []
    for j in range(nb_essais):
        if j < len(veh_data["essais"]):
            essai_data = veh_data["essais"][j]
        else:
            essai_data = {"nom": f"Test {j+1}", "interlocuteur": f"Interlocuteur {j+1}", "duree": 2, "date_debut": str(datetime.today().date())}

        nom_test = st.sidebar.text_input(f"Nom du test {j+1} ({id_veh})", value=essai_data["nom"], key=f"nom_test_{i}_{j}")
        interlocuteur = st.sidebar.text_input(f"Interlocuteur du test {nom_test} ({id_veh})", value=essai_data["interlocuteur"], key=f"interlocuteur_{i}_{j}")
        duree = st.sidebar.number_input(f"Durée (jours) du test {nom_test} ({id_veh})", min_value=1, max_value=30, value=int(essai_data["duree"]), key=f"duree_{i}_{j}")
        date_debut = st.sidebar.date_input(f"Date de début du test {nom_test} ({id_veh})", value=pd.to_datetime(essai_data["date_debut"]).date(), key=f"date_debut_{i}_{j}")
        essais.append({
            "nom": nom_test,
            "duree": duree,
            "interlocuteur": interlocuteur,
            "date_debut": str(date_debut)
        })

    vehicules.append({
        "id": id_veh,
        "sopm": str(sopm),
        "lrm": str(lrm),
        "essais": essais
    })

# 💾 Sauvegarde du projet
if st.sidebar.button("💾 Sauvegarder le projet"):
    with open(os.path.join(DOSSIER_PROJETS, f"{nom_projet}.json"), "w") as f:
        json.dump({"vehicules": vehicules}, f, indent=2)
    st.sidebar.success(f"Projet '{nom_projet}' sauvegardé avec succès ✅")

# ⚠️ Détection des chevauchements
chevauchements = []
for veh in vehicules:
    essais = veh["essais"]
    for i in range(len(essais)):
        debut_i = pd.to_datetime(essais[i]["date_debut"]).date()
        duree_i = int(essais[i]["duree"])
        fin_i = debut_i + timedelta(days=duree_i - 1)

        for j in range(i + 1, len(essais)):
            debut_j = pd.to_datetime(essais[j]["date_debut"]).date()
            duree_j = int(essais[j]["duree"])
            fin_j = debut_j + timedelta(days=duree_j - 1)

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
    for veh in vehicules:
        for test in veh["essais"]:
            # Affiche uniquement les essais bien définis
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
