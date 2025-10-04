import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from io import BytesIO
import plotly.express as px

# -----------------------------
# Initialisation DB SQLite avec migration automatique
# -----------------------------
def init_db():
    conn = sqlite3.connect("planning.db")
    c = conn.cursor()

    # Création des tables si elles n'existent pas
    c.execute('''CREATE TABLE IF NOT EXISTS projets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom_projet TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS vehicules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    veh_id TEXT,
                    contremarque TEXT,
                    vis TEXT,
                    vin TEXT,
                    sopm DATE,
                    projet_id INTEGER)''')

    c.execute('''CREATE TABLE IF NOT EXISTS essais (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vehicule_id INTEGER,
                    nom_test TEXT,
                    interlocuteur TEXT,
                    date_debut DATE,
                    duree INTEGER,
                    essai_suivant TEXT)''')

    conn.commit()
    return conn

conn = init_db()

# -----------------------------
# Fonctions utilitaires
# -----------------------------
def convert_df_to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Planning')
    return output.getvalue()

def get_all_planning(projet_id=None, start_date=None, end_date=None):
    query = """SELECT p.nom_projet, v.id as veh_db_id, v.veh_id, v.contremarque, v.vis, v.vin, v.sopm,
                      e.id as essai_id, e.nom_test, e.interlocuteur, e.date_debut, e.duree, e.essai_suivant
               FROM essais e 
               JOIN vehicules v ON e.vehicule_id = v.id
               JOIN projets p ON v.projet_id = p.id"""
    conditions = []
    if projet_id:
        conditions.append(f"p.id={projet_id}")
    if start_date and end_date:
        conditions.append(f"date(e.date_debut) BETWEEN date('{start_date}') AND date('{end_date}')")
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    df = pd.read_sql_query(query, conn)
    if not df.empty:
        df["Date Début"] = pd.to_datetime(df["date_debut"])
        df["Date Fin"] = df["Date Début"] + pd.to_timedelta(df["duree"] - 1, unit="D")
        df["Alerte Fin"] = df["Date Fin"].apply(lambda x: "🔔" if (x.date() - datetime.today().date()).days <= 7 else "")
        df.rename(columns={"nom_projet": "Projet", "veh_id": "ID Véhicule", "contremarque": "Contremarque",
                           "vis": "VIS", "vin": "VIN", "nom_test": "Nom d'essai", "interlocuteur": "Interlocuteur d'essai",
                           "essai_suivant": "Essai suivant", "sopm": "Date SOPM"}, inplace=True)
    return df

def detect_chevauchements(df):
    chevauchements = []
    for veh in df["ID Véhicule"].unique():
        essais = df[df["ID Véhicule"] == veh].sort_values("Date Début")
        for i in range(len(essais) - 1):
            fin = essais.iloc[i]["Date Fin"]
            debut = essais.iloc[i + 1]["Date Début"]
            if debut <= fin:
                chevauchements.append(
                    f"⚠️ Chevauchement sur {veh} entre \"{essais.iloc[i]['Nom d\\'essai']}\" et \"{essais.iloc[i + 1]['Nom d\\'essai']}\""
                )
    return chevauchements

# -----------------------------
# Interface Streamlit
# -----------------------------
st.set_page_config(page_title="Planification des essais véhicules", layout="wide")
st.title("🚗 Planification des essais par projet")

mode = st.radio("Mode :", ["Créer un nouveau projet", "Gérer / Modifier un projet existant"])

# -----------------------------
# Mode Création
# -----------------------------
if mode == "Créer un nouveau projet":
    nom_projet = st.text_input("Nom du projet :", placeholder="Ex: SOPM Octobre 2025")
    if nom_projet:
        st.sidebar.header("📋 Configuration des véhicules")
        nb_vehicules = st.sidebar.number_input("Nombre de véhicules", min_value=1, max_value=20, value=2)

        vehicules = []
        for i in range(nb_vehicules):
            st.sidebar.subheader(f"Véhicule {i+1}")
            id_veh = st.sidebar.text_input(f"ID Véhicule {i+1}", value=f"V{i+1:03}")
            contremarque = st.sidebar.text_input(f"Contremarque {id_veh}", key=f"cm_{i}")
            vis = st.sidebar.text_input(f"VIS {id_veh}", key=f"vis_{i}")
            vin = st.sidebar.text_input(f"VIN {id_veh}", key=f"vin_{i}")
            sopm = st.sidebar.date_input(f"Date SOPM {id_veh}", key=f"sopm_{i}")
            nb_essais = st.sidebar.number_input(f"Nombre d'essais pour {id_veh}", min_value=1, max_value=10, value=2, key=f"nb_essais_{i}")

            essais = []
            for j in range(nb_essais):
                nom_test = st.sidebar.text_input(f"Nom du test {j+1} ({id_veh})", value=f"Test {j+1}", key=f"nom_{i}_{j}")
                interlocuteur = st.sidebar.text_input(f"Interlocuteur {nom_test}", value=f"Interlocuteur {j+1}", key=f"interloc_{i}_{j}")
                duree = st.sidebar.number_input(f"Durée (jours) {nom_test}", min_value=1, max_value=30, value=2, key=f"duree_{i}_{j}")
                date_debut = st.sidebar.date_input(f"Date début {nom_test}", key=f"date_{i}_{j}")
                essai_suivant = st.sidebar.text_input(f"Essai suivant {nom_test}", value="", key=f"suivant_{i}_{j}")
                essais.append({"nom": nom_test, "interlocuteur": interlocuteur, "duree": duree,
                               "date_debut": date_debut, "essai_suivant": essai_suivant})
            vehicules.append({"id": id_veh, "contremarque": contremarque, "vis": vis, "vin": vin,
                              "sopm": sopm, "essais": essais})

        if st.button("📅 Sauvegarder le projet"):
            c = conn.cursor()
            c.execute("INSERT INTO projets (nom_projet) VALUES (?)", (nom_projet,))
            projet_id = c.lastrowid

            planning = []
            for veh in vehicules:
                c.execute("INSERT INTO vehicules (veh_id, contremarque, vis, vin, sopm, projet_id) VALUES (?, ?, ?, ?, ?, ?)",
                          (veh["id"], veh["contremarque"], veh["vis"], veh["vin"], veh["sopm"], projet_id))
                veh_id_db = c.lastrowid

                for test in veh["essais"]:
                    date_fin = test["date_debut"] + timedelta(days=test["duree"] - 1)
                    c.execute("INSERT INTO essais (vehicule_id, nom_test, interlocuteur, date_debut, duree, essai_suivant) VALUES (?, ?, ?, ?, ?, ?)",
                              (veh_id_db, test["nom"], test["interlocuteur"], test["date_debut"], test["duree"], test["essai_suivant"]))
                    planning.append({
                        "Projet": nom_projet,
                        "Contremarque": veh["contremarque"],
                        "VIS": veh["vis"],
                        "VIN": veh["vin"],
                        "Nom d'essai": test["nom"],
                        "Interlocuteur d'essai": test["interlocuteur"],
                        "Date Début": test["date_debut"],
                        "Date Fin": date_fin,
                        "Essai suivant": test["essai_suivant"],
                        "Date SOPM": veh["sopm"],
                        "Alerte Fin": "🔔" if (date_fin - datetime.today().date()).days <= 7 else ""
                    })

            conn.commit()
            df = pd.DataFrame(planning)
            st.success(f"✅ Projet '{nom_projet}' sauvegardé avec succès !")

            # Tableau
            st.subheader("📄 Tableau du planning")
            st.dataframe(df)

            # Gantt
            st.subheader("📊 Visualisation Gantt")
            fig = px.timeline(
                df,
                x_start="Date Début",
                x_end="Date Fin",
                y="Contremarque",
                color="Nom d'essai",
                text="Nom d'essai",
                hover_data=["Interlocuteur d'essai", "Essai suivant", "Date SOPM", "Alerte Fin"]
            )
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)

            # Export Excel
            excel_data = convert_df_to_excel(df)
            st.download_button("📥 Télécharger Excel", excel_data, f"planning_{nom_projet}.xlsx")

            # Chevauchements
            chevauchements = detect_chevauchements(df)
            if chevauchements:
                st.error("⚠️ Chevauchements détectés :")
                for c in chevauchements:
                    st.write(c)
