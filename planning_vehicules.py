import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import datetime, timedelta
from io import BytesIO

# -----------------------------
# Initialisation DB SQLite avec mise à jour
# -----------------------------
def init_db():
    conn = sqlite3.connect("planning.db")
    c = conn.cursor()
    # Création des tables si elles n'existent pas
    c.execute('''CREATE TABLE IF NOT EXISTS vehicules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    veh_id TEXT,
                    sopm DATE,
                    lrm DATE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS essais (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vehicule_id INTEGER,
                    nom_test TEXT,
                    date_debut DATE,
                    duree INTEGER,
                    FOREIGN KEY(vehicule_id) REFERENCES vehicules(id))''')
    conn.commit()

    # Ajout de la colonne interlocuteur si elle n'existe pas
    try:
        c.execute("ALTER TABLE essais ADD COLUMN interlocuteur TEXT;")
    except sqlite3.OperationalError:
        pass  # Colonne déjà existante
    return conn

conn = init_db()

# -----------------------------
# Interface Streamlit
# -----------------------------
st.set_page_config(page_title="Planification des essais véhicules", layout="wide")
st.title("🚗 Planification des essais des véhicules")

mode = st.radio("Mode :", ["Créer un nouveau planning", "Charger un planning existant"])

if mode == "Créer un nouveau planning":
    st.sidebar.header("📋 Configuration des véhicules")
    nb_vehicules = st.sidebar.number_input("Nombre de véhicules", min_value=1, max_value=20, value=2)

    vehicules = []
    for i in range(nb_vehicules):
        st.sidebar.subheader(f"Véhicule {i+1}")
        id_veh = st.sidebar.text_input(f"ID Véhicule {i+1}", value=f"V{i+1:03}")
        sopm = st.sidebar.date_input(f"Date SOPM {id_veh}", key=f"sopm_{i}")
        lrm = st.sidebar.date_input(f"Date LRM {id_veh}", key=f"lrm_{i}")
        nb_essais = st.sidebar.number_input(f"Nombre d'essais pour {id_veh}", min_value=1, max_value=10, value=2, key=f"nb_essais_{i}")

        essais = []
        for j in range(nb_essais):
            nom_test = st.sidebar.text_input(f"Nom du test {j+1} ({id_veh})", value=f"Test {j+1}", key=f"nom_{i}_{j}")
            interlocuteur = st.sidebar.text_input(f"Interlocuteur {nom_test}", value=f"Interlocuteur {j+1}", key=f"interloc_{i}_{j}")
            duree = st.sidebar.number_input(f"Durée (jours) {nom_test}", min_value=1, max_value=30, value=2, key=f"duree_{i}_{j}")
            date_debut = st.sidebar.date_input(f"Date début {nom_test}", key=f"date_{i}_{j}")
            essais.append({"nom": nom_test, "interlocuteur": interlocuteur, "duree": duree, "date_debut": date_debut})
        vehicules.append({"id": id_veh, "sopm": sopm, "lrm": lrm, "essais": essais})

    if st.button("📅 Générer et Sauvegarder le planning"):
        planning = []
        chevauchements = []
        today = datetime.today().date()

        for veh in vehicules:
            c = conn.cursor()
            c.execute("INSERT INTO vehicules (veh_id, sopm, lrm) VALUES (?, ?, ?)", (veh["id"], veh["sopm"], veh["lrm"]))
            veh_id_db = c.lastrowid

            intervals = []
            for test in veh["essais"]:
                date_debut = test["date_debut"]
                date_fin = date_debut + timedelta(days=test["duree"] - 1)
                semaine = date_debut.isocalendar()[1]

                # Vérification chevauchement
                for (start, end, nom) in intervals:
                    if (date_debut <= end and date_fin >= start):
                        chevauchements.append(f"⚠️ Chevauchement sur {veh['id']} entre {nom} et {test['nom']}")
                intervals.append((date_debut, date_fin, test["nom"]))

                c.execute("INSERT INTO essais (vehicule_id, nom_test, interlocuteur, date_debut, duree) VALUES (?, ?, ?, ?, ?)",
                          (veh_id_db, test["nom"], test["interlocuteur"], date_debut, test["duree"]))

                planning.append({
                    "ID Véhicule": veh["id"],
                    "Nom du Test": test["nom"],
                    "Interlocuteur": test["interlocuteur"],
                    "Date Début": date_debut,
                    "Date Fin": date_fin,
                    "Durée (jours)": test["duree"],
                    "Semaine": semaine,
                    "Date SOPM": veh["sopm"],
                    "Date LRM": veh["lrm"],
                    "Alerte Fin Test": "🔔" if (date_fin - today).days <= 2 else ""
                })

            conn.commit()

        df = pd.DataFrame(planning)
        st.success("✅ Planning sauvegardé et généré avec succès !")

        if chevauchements:
            st.error("⚠️ Chevauchements détectés :")
            for c in chevauchements:
                st.write(c)

        # Tableau complet
        st.subheader("📄 Tableau du planning")
        st.dataframe(df)

        # Gantt avec hover complet et labels
        st.subheader("📊 Visualisation Gantt")
        fig = px.timeline(
            df,
            x_start="Date Début",
            x_end="Date Fin",
            y="ID Véhicule",
            color="Nom du Test",
            text="Nom du Test",
            hover_data=[
                "Nom du Test", "Interlocuteur", "Durée (jours)", "Semaine",
                "Date SOPM", "Date LRM", "Alerte Fin Test"
            ]
        )
        fig.update_traces(textposition='inside', insidetextanchor='start')
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(title="Planning des essais par véhicule", xaxis_title="Date", yaxis_title="Véhicule")
        st.plotly_chart(fig, use_container_width=True)

        # Export Excel
        def convert_df_to_excel(df):
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Planning')
            return output.getvalue()

        excel_data = convert_df_to_excel(df)
        st.download_button("📥 Télécharger Excel", excel_data, "planning.xlsx")

else:
    st.subheader("📂 Charger un planning existant")
    c = conn.cursor()
    c.execute("SELECT id, veh_id FROM vehicules")
    veh_list = c.fetchall()
    if veh_list:
        choix = st.selectbox("Choisir un véhicule :", [f"{v[0]} - {v[1]}" for v in veh_list])
        veh_id = int(choix.split(" - ")[0])
        c.execute("SELECT nom_test, interlocuteur, date_debut, duree FROM essais WHERE vehicule_id=?", (veh_id,))
        essais = c.fetchall()
        df = pd.DataFrame(essais, columns=["Nom du Test", "Interlocuteur", "Date Début", "Durée (jours)"])
        st.dataframe(df)
    else:
        st.warning("Aucun planning trouvé dans la base.")
