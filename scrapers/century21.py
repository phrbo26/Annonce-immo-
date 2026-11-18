"""Annonces Century 21 : page par commune, ex. century21.fr/annonces/achat-maison/v-donzere/
(la page inclut les communes voisines). Agence locale : Century 21 Portes de Provence (Montélimar)."""
import re
import time

import requests
from bs4 import BeautifulSoup

from commun import HEADERS, echantillon, enregistrer, lien_absolu, nombre, photo, prix_isole, remonter_carte, trouver_commune

COMMUNES = ["donzere", "pierrelatte", "montelimar", "saint-paul-trois-chateaux", "viviers", "malataverne"]
BASE = "https://www.century21.fr"


def lire_commune(commune):
    r = requests.get(f"{BASE}/annonces/achat-maison/v-{commune}/", headers=HEADERS, timeout=30)
    if r.status_code == 404:
        return []
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    annonces = {}
    for a in soup.select('a[href*="/trouver_logement/detail/"]'):
        m = re.search(r"/detail/(\d+)", a["href"])
        if not m or ("c21-" + m.group(1)) in annonces:
            continue
        carte = remonter_carte(a)
        echantillon("century21-carte", carte)
        texte = carte.get_text(" ", strip=True)
        img = carte.find("img")
        alt = img.get("alt", "") if img else ""
        commune = trouver_commune(alt, texte)
        annonces["c21-" + m.group(1)] = {
            "ref": "c21-" + m.group(1),
            "titre": (alt or "Maison") + (" – " + texte[:60] if not alt else ""),
            "lien": lien_absolu(BASE, a["href"]),
            "prix": prix_isole(carte),
            "surface": nombre(r"([\d,]+)\s?m\s?2", texte),
            "pieces": nombre(r"(\d+)\s?(?:pcs|pièces)", texte),
            "chambres": nombre(r"(\d+)\s?chambres?", texte),
            "lieu": None,
            "commune": commune[0] if commune else None,
            "photo": photo(carte, BASE),
        }
    if not annonces:
        echantillon("century21-page-vide", r.text)
    return list(annonces.values())


def main():
    trouvees = {}
    for commune in COMMUNES:
        try:
            for x in lire_commune(commune):
                trouvees[x["ref"]] = x
        except Exception as e:
            print("Erreur", commune, e)
        time.sleep(3)
    enregistrer("Century 21", list(trouvees.values()), garder_inconnues=False)


if __name__ == "__main__":
    main()
