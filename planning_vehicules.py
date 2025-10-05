import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from io import BytesIO

st.set_page_config(page_title="Planification des essais véhicules", layout="wide")
st.title("🚗 Planification des essais des véhicules")

# 📋 Données des véhicules avec essais spécifiques
st.sidebar.header("📋 Données des véhicules")
vehicules = []
nb_vehicules = st.sidebar.number_input("Nombre de véhicules", min_value=1, max_value=20, value=2)

for i in range(nb_vehicules):
    st.sidebar.subheader(f"Véhicule {i+1}")
    id_veh = st.sidebar.text_input(f"ID Véhicule {i+1}", value=f"V{i+1:03}")
    sopm = st.sidebar.date_input(f"Date SOPM {id_veh}", key=f"sopm_{i}")
    lrm = st.sidebar.date_input(f"Date LRM {id_veh}", key=f"lrm_{i}")

    st.sidebar.markdown(f"**Essais pour {id_veh}**")
    nb_essais = st.sidebar.number_input(f"Nombre d'essais pour {id_veh}", min_value=1, max_value=10, value=2, key=f"nb_essais_{i}")
    essais = []
    for j in range(nb_essais):
        nom_test = st.sidebar.text_input(f"Nom du test {j+1} ({id_veh})", value=f"Test {j+1}", key=f"nom_test_{i}_{j}")
        interlocuteur = st.sidebar.text_input(f"Interlocuteur du test {nom_test} ({id_veh})", value=f"Interlocuteur {j+1}", key=f"interlocuteur_{i}_{j}")
        duree = st.sidebar.number_input(f"Durée (jours) du test {nom_test} ({id_veh})", min_value=1, max_value=30, value=2, key=f"duree_{i}_{j}")
        date_debut = st.sidebar.date_input(f"Date de début du test {nom_test} ({id_veh})", key=f"date_debut_{i}_{j}")
        essais.append({
            "nom": nom_test,
            "duree": duree,
            "interlocuteur": interlocuteur,
            "date_debut": date_debut
        })

    vehicules.append({
        "id": id_veh,
        "sopm": sopm,
        "lrm": lrm,
        "essais": essais
    })

# ⚠️ Vérification des chevauchements
chevauchements = []
for veh in vehicules:
    essais = veh["essais"]
    for i in range(len(essais)):
        debut_i = essais[i]["date_debut"]
        fin_i = debut_i + timedelta(days=essais[i]["duree"] - 1)
        for j in range(i + 1, len(essais)):
            debut_j = essais[j]["date_debut"]
            fin_j = debut_j + timedelta(days=essais[j]["duree"] - 1)
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
            date_debut = test["date_debut"]
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
        file_name="planning_essais_vehicules.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
