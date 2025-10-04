import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import datetime, timedelta
from io import BytesIO

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
                    sopm DATE,
                    lrm DATE)''')

    c.execute('''CREATE TABLE IF NOT EXISTS essais (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vehicule_id INTEGER,
                    nom_test TEXT,
                    date_debut DATE,
                    duree INTEGER)''')

    conn.commit()
    st.experimental_rerun()

    # Migration : ajout des colonnes manquantes
    try:
        c.execute("ALTER TABLE vehicules ADD COLUMN projet_id INTEGER;")
    except sqlite3.OperationalError:
        pass

    try:
        c.execute("ALTER TABLE essais ADD COLUMN interlocuteur TEXT;")
    except sqlite3.OperationalError:
        pass

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
    query = """SELECT p.nom_projet, v.id as veh_db_id, v.veh_id, v.sopm, v.lrm,
                      e.id as essai_id, e.nom_test, e.interlocuteur, e.date_debut, e.duree
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
        df.rename(columns={"nom_projet": "Projet", "veh_id": "ID Véhicule", "nom_test": "Nom du Test",
                           "interlocuteur": "Interlocuteur", "duree": "Durée (jours)", "sopm": "Date SOPM",
                           "lrm": "Date LRM"}, inplace=True)
    return df

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

        if st.button("📅 Sauvegarder le projet"):
            c = conn.cursor()
            c.execute("INSERT INTO projets (nom_projet) VALUES (?)", (nom_projet,))
            projet_id = c.lastrowid

            planning = []
            chevauchements = []
            today = datetime.today().date()

            for veh in vehicules:
                c.execute("INSERT INTO vehicules (projet_id, veh_id, sopm, lrm) VALUES (?, ?, ?, ?)",
                          (projet_id, veh["id"], veh["sopm"], veh["lrm"]))
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
                        "Projet": nom_projet,
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
    st.experimental_rerun()
            df = pd.DataFrame(planning)
            st.success(f"✅ Projet '{nom_projet}' sauvegardé avec succès !")

            if chevauchements:
                st.error("⚠️ Chevauchements détectés :")
                for c in chevauchements:
                    st.write(c)

            # Tableau
            st.subheader("📄 Tableau du planning")
            st.dataframe(df)

            # Gantt
            st.subheader("📊 Visualisation Gantt")
            fig = px.timeline(
                df,
                x_start="Date Début",
                x_end="Date Fin",
                y="ID Véhicule",
                color="Nom du Test",
                text="Nom du Test",
                hover_data=["Interlocuteur", "Durée (jours)", "Date SOPM", "Date LRM"]
            )
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)

            # Export Excel
            excel_data = convert_df_to_excel(df)
            st.download_button("📥 Télécharger Excel", excel_data, f"planning_{nom_projet}.xlsx")

# -----------------------------
# Mode Gestion / Modification
# -----------------------------
else:
    st.subheader("📂 Modifier un projet existant")
    projets = pd.read_sql_query("SELECT * FROM projets", conn)
    if not projets.empty:
        choix_projet = st.selectbox("Choisir un projet :", projets["nom_projet"].tolist())
        projet_id = projets.loc[projets["nom_projet"] == choix_projet, "id"].values[0]

        # Filtre par période
        st.write("📅 Filtrer par période")
        start_date = st.date_input("Date début", value=datetime.today() - timedelta(days=30))
        end_date = st.date_input("Date fin", value=datetime.today() + timedelta(days=30))

        df = get_all_planning(projet_id, start_date, end_date)
        if not df.empty:
            st.write(f"Planning du projet **{choix_projet}**")
            st.dataframe(df)

            # Gantt
            st.subheader("📊 Visualisation Gantt")
            fig = px.timeline(
                df,
                x_start="Date Début",
                x_end="Date Fin",
                y="ID Véhicule",
                color="Nom du Test",
                text="Nom du Test",
                hover_data=["Interlocuteur", "Durée (jours)", "Date SOPM", "Date LRM"]
            )
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)

            # Export Excel
            excel_data = convert_df_to_excel(df)
            st.download_button("📥 Télécharger Excel", excel_data, f"planning_{choix_projet}.xlsx")

            # Ajout d'un nouveau véhicule
            st.subheader("➕ Ajouter un nouveau véhicule")
            new_veh_id = st.text_input("ID du nouveau véhicule")
            new_sopm = st.date_input("Date SOPM du véhicule")
            new_lrm = st.date_input("Date LRM du véhicule")
            if st.button("Ajouter véhicule"):
                conn.execute("INSERT INTO vehicules (projet_id, veh_id, sopm, lrm) VALUES (?, ?, ?, ?)",
                             (projet_id, new_veh_id, new_sopm, new_lrm))
                conn.commit()
    st.experimental_rerun()
                st.success("Véhicule ajouté avec succès !")

            # Ajout d'un nouvel essai
            st.subheader("➕ Ajouter un nouvel essai")
        # Charger tous les véhicules du projet, même ceux sans essais
        vehicules_existants_query = pd.read_sql_query(
            "SELECT veh_id, id as veh_db_id FROM vehicules WHERE projet_id=?",
            conn, params=(projet_id,)
        )
        vehicules_existants = vehicules_existants_query["veh_id"].tolist()
        vehicule_cible = st.selectbox("Choisir un véhicule :", vehicules_existants)
        nom_test = st.text_input("Nom du test")
        interlocuteur = st.text_input("Interlocuteur")
        date_debut = st.date_input("Date début")
        duree = st.number_input("Durée (jours)", min_value=1, max_value=30, value=2)
        if st.button("Ajouter essai"):
            veh_db_id = vehicules_existants_query.loc[
                vehicules_existants_query["veh_id"] == vehicule_cible, "veh_db_id"
            ].iloc[0]
            conn.execute("INSERT INTO essais (vehicule_id, nom_test, interlocuteur, date_debut, duree) VALUES (?, ?, ?, ?, ?)",
                         (veh_db_id, nom_test, interlocuteur, date_debut, duree))
            conn.commit()
            st.success("Essai ajouté avec succès !")
            st.experimental_rerun()
            nom_test = st.text_input("Nom du test")
            interlocuteur = st.text_input("Interlocuteur")
            date_debut = st.date_input("Date début")
            duree = st.number_input("Durée (jours)", min_value=1, max_value=30, value=2)
            if st.button("Ajouter essai"):
                veh_db_id = df[df["ID Véhicule"] == vehicule_cible]["veh_db_id"].iloc[0]
                conn.execute("INSERT INTO essais (vehicule_id, nom_test, interlocuteur, date_debut, duree) VALUES (?, ?, ?, ?, ?)",
                             (veh_db_id, nom_test, interlocuteur, date_debut, duree))
                conn.commit()
    st.experimental_rerun()
                st.success("Essai ajouté avec succès !")

            # Supprimer un véhicule
            st.subheader("🗑 Supprimer un véhicule")
            vehicule_suppr = st.selectbox("Choisir un véhicule à supprimer :", vehicules_existants)
            if st.button("Supprimer véhicule"):
                veh_db_id = df[df["ID Véhicule"] == vehicule_suppr]["veh_db_id"].iloc[0]
                conn.execute("DELETE FROM essais WHERE vehicule_id=?", (veh_db_id,))
                conn.execute("DELETE FROM vehicules WHERE id=?", (veh_db_id,))
                conn.commit()
    st.experimental_rerun()
                st.warning("Véhicule supprimé avec succès !")

            # Supprimer projet complet
            if st.button("🗑 Supprimer le projet complet"):
                conn.execute("DELETE FROM projets WHERE id=?", (projet_id,))
                conn.execute("DELETE FROM vehicules WHERE projet_id=?", (projet_id,))
                conn.commit()
    st.experimental_rerun()
                st.error("Projet supprimé avec succès !")
        else:
            st.info("Aucun essai pour ce projet.")
    else:
        st.warning("Aucun projet trouvé.")
