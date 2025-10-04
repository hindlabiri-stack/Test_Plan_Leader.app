import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from io import BytesIO

# Configuration de la page
st.set_page_config(page_title="Planification des essais véhicules", layout="wide")
st.title("🚗 Planification des essais des véhicules")
st.sidebar.subheader("📂 Charger un projet existant")
liste_projets = [f.split(".")[0] for f in os.listdir("projets") if f.endswith(".json")]
projet_selectionne = st.sidebar.selectbox("Sélectionner un projet", options=[""] + liste_projets)

if projet_selectionne:
    with open(f"projets/{projet_selectionne}.json", "r", encoding="utf-8") as f:
        projet_charge = json.load(f)
    nom_projet = projet_charge["nom"]
    description_projet = projet_charge["description"]
    vehicules = projet_charge["vehicules"]
    essais = projet_charge["essais"]
    st.sidebar.success(f"📂 Projet '{nom_projet}' chargé")
# 📋 Saisie des données des véhicules
st.sidebar.header("📋 Données des véhicules")
vehicules = []
nb_vehicules = st.sidebar.number_input("Nombre de véhicules", min_value=1, max_value=20, value=2)

for i in range(nb_vehicules):
    st.sidebar.subheader(f"Véhicule {i+1}")
    id_veh = st.sidebar.text_input(f"ID Véhicule {i+1}", value=f"V{i+1:03}")
    sopm = st.sidebar.date_input(f"Date SOPM {id_veh}", key=f"sopm_{i}")
    lrm = st.sidebar.date_input(f"Date LRM {id_veh}", key=f"lrm_{i}")
    vehicules.append({"id": id_veh, "sopm": sopm, "lrm": lrm})

# 🧪 Saisie des essais
st.sidebar.header("🧪 Définition des essais")
essais = []
nb_essais = st.sidebar.number_input("Nombre de types d'essais", min_value=1, max_value=10, value=3)

for j in range(nb_essais):
    nom_test = st.sidebar.text_input(f"Nom du test {j+1}", value=f"Test {j+1}")
    interlocuteur = st.sidebar.text_input(f"Interlocuteur du test {nom_test}", value=f"Interlocuteur {j+1}")
    duree = st.sidebar.number_input(f"Durée (jours) du test {nom_test}", min_value=1, max_value=30, value=2, key=f"duree_{j}")
    essais.append({"nom": nom_test, "duree": duree, "interlocuteur": interlocuteur})

# 📅 Génération du planning
if st.button("📅 Générer le planning"):
    planning = []
    today = datetime.today().date()
    for veh in vehicules:
        date_courante = veh["sopm"]
        for test in essais:
            date_debut = date_courante
            date_fin = date_debut + timedelta(days=test["duree"] - 1)
            semaine = date_debut.isocalendar()[1]
            alerte_sopm = "⚠️" if (veh["sopm"] - today).days <= 3 else ""
            alerte_lrm = "⚠️" if (veh["lrm"] - today).days <= 3 else ""
            alerte_fin_test = "🔔" if (date_fin - today).days <= 2 else ""
            planning.append({
                "ID Véhicule": veh["id"],
                "Nom du Test": test["nom"],
                "Interlocuteur": test["interlocuteur"],
                "Date Début": date_debut,
                "Date Fin": date_fin,
                "Durée (jours)": test["duree"],
                "Semaine": semaine,
                "Date SOPM": f"{veh['sopm']} {alerte_sopm}",
                "Date LRM": f"{veh['lrm']} {alerte_lrm}",
                "Alerte Fin Test": alerte_fin_test
            })
            date_courante = date_fin + timedelta(days=1)

    df = pd.DataFrame(planning)
    st.success("✅ Planning généré avec succès !")

    # 📊 Affichage du tableau
    st.subheader("📊 Tableau du planning")
    st.dataframe(df)

    # 📈 Visualisation Gantt
    st.subheader("📈 Visualisation Gantt")
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

    # 📥 Export Excel
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
