def extraire_dates(prompt):
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
          
