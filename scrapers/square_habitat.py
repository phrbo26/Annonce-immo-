"""Annonces Square Habitat (Crédit Agricole) : page par commune, ex.
squarehabitat.fr/annonces/achat/bien/maison/immobilier/auvergne-rhone-alpes/drome/montelimar-26200
Agence locale : Square Habitat Sud Rhône-Alpes, place du Théâtre à Montélimar."""
import re
import time

import requests
from bs4 import BeautifulSoup

from commun import HEADERS, echantillon, enregistrer, lien_absolu, nombre, photo, remonter_carte, trouver_commune

PAGES = [
    "drome/montelimar-26200", "drome/pierrelatte-26700", "drome/donzere-26290",
    "drome/saint-paul-trois-chateaux-26130", "ardeche/viviers-07220",
]
BASE = "https://www.squarehabitat.fr"


def lire(page):
    r = requests.get(f"{BASE}/annonces/achat/bien/maison/immobilier/auvergne-rhone-alpes/{page}", headers=HEADERS, timeout=30)
    if r.status_code == 404:
        return []
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    annonces = {}
    for a in soup.select('a[href*="/annonces/biens/achat"]'):
        m = re.search(r"/([0-9a-f]{8}-[0-9a-f-]{27})", a["href"])
        if not m or ("sqh-" + m.group(1)) in annonces:
            continue
        carte = remonter_carte(a)
        echantillon("square_habitat-carte", carte)
        texte = carte.get_text(" ", strip=True)
        commune = trouver_commune(a["href"], texte)
        titre = re.search(r"(Maison à vendre - [^,]+, \d+ pièces)", texte)
        annonces["sqh-" + m.group(1)] = {
            "ref": "sqh-" + m.group(1),
            "titre": titre.group(1).title().replace("À Vendre", "à vendre") if titre else texte[:80],
            "lien": lien_absolu(BASE, a["href"]),
            "prix": nombre(r"Au prix de\s*([\d\s  ]+)", texte),
            "surface": nombre(r"(\d+)\s?m²\s*habitable", texte) or nombre(r"surface habitable[^\d]{0,20}(\d+)", texte),
            "pieces": nombre(r"(\d+)\s?pièces", texte),
            "chambres": nombre(r"(\d+)\s?chambres", texte),
            "lieu": None,
            "commune": commune[0] if commune else None,
            "photo": photo(carte, BASE),
        }
    return list(annonces.values())


def main():
    trouvees = {}
    for page in PAGES:
        try:
            for x in lire(page):
                trouvees[x["ref"]] = x
        except Exception as e:
            print("Erreur", page, e)
        time.sleep(3)
    enregistrer("Square Habitat", list(trouvees.values()), garder_inconnues=False)


if __name__ == "__main__":
    main()
