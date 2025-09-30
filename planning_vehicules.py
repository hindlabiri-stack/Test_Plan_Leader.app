import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="Planification des essais véhicules", layout="wide")

st.title("🚗 Planification des essais des véhicules")

st.sidebar.header("📋 Données des véhicules")

# Entrée des données des véhicules
vehicules = []
nb_vehicules = st.sidebar.number_input("Nombre de véhicules", min_value=1, max_value=20, value=2)

for i in range(nb_vehicules):
    st.sidebar.subheader(f"Véhicule {i+1}")
    id_veh = st.sidebar.text_input(f"ID Véhicule {i+1}", value=f"V{i+1:03}")
    sopm = st.sidebar.date_input(f"Date SOPM {id_veh}", key=f"sopm_{i}")
    lrm = st.sidebar.date_input(f"Date LRM {id_veh}", key=f"lrm_{i}")
    vehicules.append({"id": id_veh, "sopm": sopm, "lrm": lrm})

st.sidebar.header("🧪 Définition des essais")

# Entrée des essais
essais = []
nb_essais = st.sidebar.number_input("Nombre de types d'essais", min_value=1, max_value=10, value=3)

for j in range(nb_essais):
    nom_test = st.sidebar.text_input(f"Nom du test {j+1}", value=f"Test {j+1}")
    duree = st.sidebar.number_input(f"Durée (jours) du test {nom_test}", min_value=1, max_value=30, value=2, key=f"duree_{j}")
    essais.append({"nom": nom_test, "duree": duree})

# Génération du planning
if st.button("📅 Générer le planning"):
    planning = []
    for veh in vehicules:
        date_courante = veh["sopm"]
        for test in essais:
            date_debut = date_courante
            date_fin = date_debut + timedelta(days=test["duree"] - 1)
            semaine = date_debut.isocalendar()[1]
            planning.append({
                "ID Véhicule": veh["id"],
                "Nom du Test": test["nom"],
                "Date Début": date_debut,
                "Date Fin": date_fin,
                "Durée (jours)": test["duree"],
                "Semaine": semaine,
                "Date SOPM": veh["sopm"],
                "Date LRM": veh["lrm"]
            })
            date_courante = date_fin + timedelta(days=1)

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
        hover_data=["Nom du Test", "Durée (jours)", "Semaine", "Date SOPM", "Date LRM"]
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(title="Planning des essais par véhicule", xaxis_title="Date", yaxis_title="Véhicule")
    st.plotly_chart(fig, use_container_width=True)

    # Export Excel
    st.subheader("📥 Exporter le planning")
    @st.cache_data
    def convert_df(df):
        return df.to_excel(index=False, engine="openpyxl")

    excel_data = convert_df(df)
    st.download_button(
        label="📥 Télécharger le fichier Excel",
        data=excel_data,
        file_name="planning_essais_vehicules.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
