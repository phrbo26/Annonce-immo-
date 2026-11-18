"""Annonces Nestenn : une page par commune, ex. nestenn.com/vente/maison/donzere-26290"""
import re
import time

import requests
from bs4 import BeautifulSoup

from commun import erreur, HEADERS, enregistrer, lien_absolu, nombre, echantillon, photo, remonter_carte

COMMUNES = [
    "donzere-26290", "les-granges-gontardes-26290", "pierrelatte-26700",
    "la-garde-adhemar-26700", "malataverne-26780", "chateauneuf-du-rhone-26780",
    "saint-paul-trois-chateaux-26130", "montelimar-26200", "viviers-07220",
    "saint-montan-07220", "roussas-26230", "valaurie-26230",
]
MAX_PAGES = 3
BASE = "https://nestenn.com"


def lire_page(url):
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    annonces = {}
    for a in soup.select('a[href*="-ref-"]'):
        lien = lien_absolu(BASE, a["href"])
        m = re.search(r"-ref-(\d+)", lien)
        if not m or ("nestenn-" + m.group(1)) in annonces:
            continue
        carte = remonter_carte(a)
        echantillon("nestenn-carte", carte)
        texte = carte.get_text(" ", strip=True)
        # Les biens vendus / plus disponibles n'ont pas de prix
        if "plus disponible" in texte or " vendu" in texte or "€" not in texte:
            continue
        lieu = re.search(r"(?<!km de )\b(\d{5} [A-ZÉÈ][A-ZÉÈ\- ]+)", texte)
        annonces["nestenn-" + m.group(1)] = {
            "ref": "nestenn-" + m.group(1),
            "titre": a.get("title") or a.get_text(strip=True),
            "lien": lien,
            "prix": nombre(r"([\d\s  ]+)\s?€", texte),
            "surface": nombre(r"(\d+)\s?m²", texte),
            "pieces": nombre(r"(\d+)\s?pièce", texte),
            "chambres": nombre(r"(\d+)\s?chambre", texte),
            "lieu": lieu.group(1) if lieu else None,
            "photo": photo(carte, BASE),
        }
    if not annonces:
        echantillon("nestenn-page-vide", r.text)
    return list(annonces.values())


def main():
    trouvees = {}
    for commune in COMMUNES:
        for page in range(1, MAX_PAGES + 1):
            url = f"{BASE}/vente/maison/{commune}?page={page}"
            try:
                lot = lire_page(url)
            except Exception as e:
                erreur(url, e)
                break
            if not lot:
                break
            nouvelles = [x for x in lot if x["ref"] not in trouvees]
            for x in lot:
                trouvees[x["ref"]] = x
            time.sleep(3)
            if not nouvelles:  # la page suivante répète la même chose
                break
    enregistrer("Nestenn", list(trouvees.values()))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        from commun import signaler
        signaler("Nestenn", "erreur", f"le script a planté : {e}"[:200])
