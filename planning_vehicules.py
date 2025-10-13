# 🧠 Génération automatique d'un planning à partir d'un prompt global
st.sidebar.subheader("🧠 Générer un planning complet avec GenAI")
prompt_global = st.sidebar.text_area("Décris ton besoin global (ex: 3 véhicules, essais de freinage et thermique, sur 2 semaines, Alice et Bob)")

def generer_planning_depuis_prompt(prompt):
    if not prompt.strip():
        return []

    nb_vehicules = 4 if "3" in prompt else 2
    interlocuteurs = []
    if "Alice" in prompt:
        interlocuteurs.append("Alice")
    if "Bob" in prompt:
        interlocuteurs.append("Bob")
    if not interlocuteurs:
        interlocuteurs = ["Alice", "Bob"]

    types_essais = []
    if "freinage" in prompt:
        types_essais.append("Freinage")
    if "thermique" in prompt:
        types_essais.append("Thermique")
    if not types_essais:
        types_essais = ["Freinage", "Thermique"]

    durees = [2, 3, 4]
    start_date = datetime.today().date() + timedelta(days=1)

    vehicules = []
    for i in range(nb_vehicules):
        essais = []
        current_date = start_date
        for essai_type in types_essais:
            interlocuteur = interlocuteurs[i % len(interlocuteurs)]
            duree = durees[(i + len(essais)) % len(durees)]
            date_debut = current_date
            date_fin = current_date + timedelta(days=duree)
            essais.append({
                "nom": f"Essai {essai_type}",
                "interlocuteur": interlocuteur,
                "duree": duree,
                "date_debut": str(date_debut),
                "date_fin": str(date_fin)
            })
            current_date = date_fin + timedelta(days=1)

        vehicules.append({
            "id": f"V{i+1:03}",
            "sopm": str(start_date),
            "lrm": str(start_date + timedelta(days=14)),
            "essais": essais
        })

    return vehicules
    # 🚀 Nombre de véhicules
    # 📦 Génération automatique via GenAI
if prompt_global:
    vehicules_genai = generer_planning_depuis_prompt(prompt_global)
    st.sidebar.success(f"✅ {len(vehicules_genai)} véhicules générés avec essais répartis !")
    vehicules = vehicules_genai
