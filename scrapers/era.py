"""Annonces ERA : recherche par commune, ex. eraimmobilier.com/acheter/Pierrelatte-c36080?display=list&page=1
Agence locale : ERA Immobilier Pierrelatte. Les identifiants de commune (c36080) sont propres à ERA."""
import re
import time

import requests
from bs4 import BeautifulSoup

from commun import HEADERS, echantillon, enregistrer, lien_absolu, nombre, photo, prix_isole, remonter_carte, trouver_commune

RECHERCHES = ["Pierrelatte-c36080"]
MAX_PAGES = 3
BASE = "https://www.eraimmobilier.com"


def lire(recherche, page):
    r = requests.get(f"{BASE}/acheter/{recherche}?display=list&page={page}", headers=HEADERS, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    annonces = {}
    for a in soup.select('a[href^="/annonces/"]'):
        m = re.search(r"/annonces/(\d+)", a["href"])
        if not m or ("era-" + m.group(1)) in annonces:
            continue
        carte = remonter_carte(a)
        echantillon("era-carte", carte)
        texte = carte.get_text(" ", strip=True).replace("EXCLUSIVITÉ sous compromis sous offre DÉJA VU", "")
        lieu = re.search(r"([a-zà-ÿ'\- ]+) \((\d{5})\)", texte)
        commune = trouver_commune(lieu.group(1) if lieu else "", texte)
        type_ = re.search(r"\b(Maison|Appartement|Terrain|Local commercial|Immeuble|Villa)\b", texte)
        annonces["era-" + m.group(1)] = {
            "ref": "era-" + m.group(1),
            "titre": f"{type_.group(1) if type_ else 'Bien'} à {commune[0] if commune else (lieu.group(1).title() if lieu else '?')}",
            "lien": lien_absolu(BASE, a["href"]),
            "prix": prix_isole(carte) or nombre(r"([\d\s  ]{4,})\s?€(?!\s?/)", texte),
            "surface": nombre(r"(\d+)\s?m²", texte) if type_ and type_.group(1) != "Terrain" else None,
            "terrain": nombre(r"(\d+)\s?m²", texte) if type_ and type_.group(1) == "Terrain" else None,
            "pieces": nombre(r"(\d+)\s?p\.", texte),
            "chambres": nombre(r"(\d+)\s?ch\.", texte),
            "lieu": None,
            "commune": commune[0] if commune else None,
            "type": {"Maison": "Maison", "Villa": "Villa", "Terrain": "Terrain", "Appartement": "Appartement",
                     "Immeuble": "Immeuble"}.get(type_.group(1) if type_ else "", "Autre"),
            "photo": photo(carte, BASE),
        }
    return list(annonces.values())


def main():
    trouvees = {}
    for recherche in RECHERCHES:
        for page in range(1, MAX_PAGES + 1):
            try:
                lot = lire(recherche, page)
            except Exception as e:
                print("Erreur", recherche, page, e)
                break
            nouvelles = [x for x in lot if x["ref"] not in trouvees]
            for x in lot:
                trouvees[x["ref"]] = x
            if not nouvelles:
                break
            time.sleep(3)
    enregistrer("ERA", list(trouvees.values()), garder_inconnues=False)


if __name__ == "__main__":
    main()
