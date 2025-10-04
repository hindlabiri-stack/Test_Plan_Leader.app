import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(page_title="Planification des essais véhicules", layout="wide")
st.title("🚗 Planification des essais des véhicules")

# -----------------------------
# 1. Définition des véhicules
# -----------------------------
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
        duree = st.sidebar.number_input(f"Durée (jours) {nom_test}", min_value=1, max_value=30, value=2, key=f"duree_{i}_{j}")
        date_debut = st.sidebar.date_input(f"Date début {nom_test}", key=f"date_{i}_{j}")
        essais.append({"nom": nom_test, "duree": duree, "date_debut": date_debut})
    vehicules.append({"id": id_veh, "sopm": sopm, "lrm": lrm, "essais": essais})

# -----------------------------
# 2. Génération du planning
# -----------------------------
if st.button("📅 Générer le planning"):
    planning = []
    today = datetime.today().date()
    chevauchements = []

    for veh in vehicules:
        intervals = []
        for test in veh["essais"]:
            date_debut = test["date_debut"]
            date_fin = date_debut + timedelta(days=test["duree"] - 1)  # Calcul auto
            semaine = date_debut.isocalendar()[1]

            # Vérification chevauchement
            for (start, end, nom) in intervals:
                if (date_debut <= end and date_fin >= start):
                    chevauchements.append(f"⚠️ Chevauchement sur {veh['id']} entre {nom} et {test['nom']}")
            intervals.append((date_debut, date_fin, test["nom"]))

            alerte_sopm = "⚠️" if (veh["sopm"] - today).days <= 3 else ""
            alerte_lrm = "⚠️" if (veh["lrm"] - today).days <= 3 else ""
            alerte_fin_test = "🔔" if (date_fin - today).days <= 2 else ""

            planning.append({
                "ID Véhicule": veh["id"],
                "Nom du Test": test["nom"],
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
        hover_data=["Nom du Test", "Durée (jours)", "Semaine", "Date SOPM", "Date LRM"]
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(title="Planning des essais par véhicule", xaxis_title="Date", yaxis_title="Véhicule")
    st.plotly_chart(fig, use_container_width=True)

    # -----------------------------
    # 3. Export Excel
    # -----------------------------
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

    # -----------------------------
    # 4. Export PDF
    # -----------------------------
    st.subheader("📄 Exporter en PDF")

    def generate_pdf(dataframe):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        elements.append(Paragraph("Planning des essais véhicules", styles['Title']))

        # Tableau PDF
        table_data = [list(dataframe.columns)] + dataframe.values.tolist()
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(table)
        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()
        return pdf

    pdf_data = generate_pdf(df)
    st.download_button(
        label="📄 Télécharger le PDF",
        data=pdf_data,
        file_name="planning_essais_vehicules.pdf",
        mime="application/pdf"
    )
