import streamlit as st
import requests

# Titre de l'application
st.title("🔍 Recherche d'options véhicule via CarAPI")

# Entrées utilisateur
make = st.text_input("Marque du véhicule (ex: Renault, Peugeot, BMW)")
year = st.number_input("Année du véhicule", min_value=1900, max_value=2025, value=2022)

# Bouton de recherche
if st.button("Rechercher les modèles disponibles"):
    if make and year:
        # URL de l'API CarAPI
        url = f"https://carapi.app/api/models?year={year}&make={make.lower()}"
        
        # Remplace 'YOUR_JWT_TOKEN' par ton vrai token JWT
        headers = {
            "accept": "application/json",
            "Authorization": "Bearer YOUR_JWT_TOKEN"
        }

        # Requête API
        response = requests.get(url, headers=headers)

        # Affichage des résultats
        if response.status_code == 200:
            models = response.json()
            if models:
                st.success(f"{len(models)} modèles trouvés pour {make} ({year})")
                for model in models:
                    st.write(f"**Modèle :** {model.get('model_name')}")
                    st.write(f"**Finition :** {model.get('trim')}")
                    st.write(f"**Type de carrosserie :** {model.get('body_type')}")
                    st.write("---")
            else:
                st.warning("Aucun modèle trouvé pour cette combinaison.")
        else:
            st.error(f"Erreur API : {response.status_code}")
    else:
        st.warning("Veuillez remplir tous les champs.")
