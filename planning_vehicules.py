import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from io import BytesIO

# Configuration de la page
st.set_page_config(page_title="Planification des essais véhicules", layout="wide")
st.title("🚗 Planification des essais des véhicules")

# Sidebar pour les données des véhicules
st.sidebar.header("📋 Données des véhicules")
vehicules = []
essais_par_vehicule = {}

nb_vehicules = st.sidebar.number_input("Nombre de véhicules", min_value=1, max_value=20, value=2)

for i in range(nb_vehicules):
    st.sidebar.subheader(f"Véhicule {i+1}")
    id_veh = st.sidebar.text_input(f"Contremarque {i+1}", value=f"V{i+1:03}")
    vin = st.sidebar.text_input(f"Numéro de VIN {i+1}", value=f"VIN{i+1:05}")
    sopm = st.sidebar.date_input(f"Date SOPM {id_veh}", key=f"sopm_{i}")
    vehicules.append({"id": id_veh, "vin": vin, "sopm": sopm})
    
    essais = []
    nb_essais = st.sidebar.number_input(f"Nombre d'essais pour {id_veh}", min_value=1, max_value=10, value=2, key=f"nb_essais_{i}")
    for j in range(nb_essais):
        nom_test = st.sidebar.text_input(f"Nom de l'essai {j+1} pour {id_veh}", value=f"Essai {j+1}", key=f"nom_test_{i}_{j}")
        interlocuteur = st.sidebar.text_input(f"Interlocuteur de l'essai {nom_test}", value=f"Interlocuteur {j+1}", key=f"interlocuteur_{i}_{j}")
        duree = st.sidebar.number_input(f"Durée (jours) de l'essai {nom_test}", min_value=1, max_value=30, value=2, key=f"duree_{i}_{j}")
        essais.append({"nom": nom_test, "duree": duree, "interlocuteur": interlocuteur})
    essais_par_vehicule[id_veh] = essais

# Génération du planning
if st.button("📅 Générer le planning"):
    planning = []
    today = datetime.today().date()
    chevauchements = []

    for veh in vehicules:
        date_courante = veh["sopm"]
        essais = essais_par_vehicule[veh["id"]]
        for idx, test in enumerate(essais):
            date_debut = date_courante
            date_fin = date_debut + timedelta(days=test["duree"] - 1)
            alerte_fin_test = "🔔" if (date_fin - today).days <= 7 else ""
            essai_suivant = essais[idx + 1]["nom"] if idx + 1 < len(essais) else "Aucun"

            # Vérification des chevauchements
            for item in planning:
                if item["Contremarque"] == veh["id"]:
                    if not (date_fin < item["Date Début"] or date_debut > item["Date Fin"]):
                        chevauchements.append((veh["id"], test["nom"], item["Nom d'essai"]))

            planning.append({
                "Nom du Projet": "Projet Essais",
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
        st.warning("⚠️ Chevauchements détectés dans les essais :")
        for chev in chevauchements:
            st.write(f"Véhicule {chev[0]} : {chev[1]} chevauche avec {chev[2]}")

    st.subheader("📊 Visualisation Gantt")
    fig = px.timeline(
        df, x_start="Date Début", x_end="Date Fin", y="Contremarque", color="Nom d'essai",
        hover_data=["Nom d'essai", "Interlocuteur d'essai", "Essai suivant", "Date SOPM", "Alerte Fin d'essai"]
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(title="Planning des essais par véhicule", xaxis_title="Date", yaxis_title="Contremarque")
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
        file_name="planning_essais_vehicules.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
