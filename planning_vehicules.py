import re
from datetime import datetime, timedelta

def extraire_noms(prompt):
    return list(set(re.findall(r'\b[A-Z][a-z]+\b', prompt)))

def extraire_types_essais(prompt):
    essais = re.findall(r'(essai|test)\s+([a-zA-Z0-9\-]+)', prompt, re.IGNORECASE)
    return [e[1] for e in essais] if essais else ["Freinage", "Thermique"]

def extraire_dates(prompt):
    # Recherche des dates au format "dd/mm/yyyy" ou "dd month" ou "le 20 octobre"
    date_patterns = [
        r'\b(\d{1,2}/\d{1,2}/\d{4})\b',
        r'\b(le\s+)?(\d{1,2})\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\b'
    ]
    dates = []
    for pattern in date_patterns:
        matches = re.findall(pattern, prompt, re.IGNORECASE)
        for match in matches:
            try:
                if '/' in match[0]:
                    dates.append(datetime.strptime(match[0], "%d/%m/%Y").date())
                else:
                    jour = int(match[1])
                    mois = match[2].lower()
                    mois_num = {
                        "janvier": 1, "février": 2, "mars": 3, "avril": 4, "mai": 5,
                        "juin": 6, "juillet": 7, "août": 8, "septembre": 9,
                        "octobre": 10, "novembre": 11, "décembre": 12
                    }[mois]
                    dates.append(datetime(datetime.today().year, mois_num, jour).date())
            except:
                continue
    return dates

def extraire_nombre_vehicules(prompt):
    match = re.search(r'(\d+)\s+véhicule', prompt, re.IGNORECASE)
    return int(match.group(1)) if match else 2

def generer_planning_depuis_prompt(prompt):
    if not prompt.strip():
        return []

    nb_vehicules = extraire_nombre_vehicules(prompt)
    interlocuteurs = extraire_noms(prompt)
    if not interlocuteurs:
        interlocuteurs = ["Alice", "Bob", "Hind"]

    types_essais = extraire_types_essais(prompt)
    dates_personnalisees = extraire_dates(prompt)
    durees = [2, 3, 4]

    start_date = dates_personnalisees[0] if dates_personnalisees else datetime.today().date() + timedelta(days=1)
    vehicules = []

    for i in range(nb_vehicules):
        essais = []
        current_date = start_date
        for j, essai_type in enumerate(types_essais):
            interlocuteur = interlocuteurs[(i + j) % len(interlocuteurs)]
            duree = durees[(i + j) % len(durees)]
            date_debut = dates_personnalisees[j] if j < len(dates_personnalisees) else current_date
            date_fin = date_debut + timedelta(days=duree)
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
