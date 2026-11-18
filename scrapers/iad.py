"""Annonces IAD : une page par commune, ex. iadfrance.fr/annonces/donzere-26290/vente/maison"""
import time

import requests
from bs4 import BeautifulSoup

from commun import HEADERS, enregistrer, lien_absolu, nombre, echantillon, photo_proche, remonter_carte

COMMUNES = [
    "donzere-26290", "les-granges-gontardes-26290", "pierrelatte-26700",
    "la-garde-adhemar-26700", "malataverne-26780", "chateauneuf-du-rhone-26780",
    "saint-paul-trois-chateaux-26130", "montelimar-26200", "viviers-07220",
    "saint-montan-07220", "roussas-26230", "valaurie-26230",
]
BASE = "https://www.iadfrance.fr"


def lire_commune(commune):
    r = requests.get(f"{BASE}/annonces/{commune}/vente/maison", headers=HEADERS, timeout=30)
    if r.status_code == 404:
        return []
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    annonces = {}
    for a in soup.select('a[href*="/annonce/maison-vente"]'):
        lien = a["href"] if a["href"].startswith("http") else BASE + a["href"]
        ref = "iad-" + lien.rstrip("/").split("/")[-1]
        if ref in annonces:
            continue
        carte = remonter_carte(a)
        echantillon("iad-carte", carte)
        texte = carte.get_text(" ", strip=True)
        if "Sous compromis" in texte:
            continue
        annonces[ref] = {
            "ref": ref,
            "titre": a.get_text(" ", strip=True),
            "lien": lien,
            "prix": nombre(r"([\d\s  ]+)\s?€", texte),
            "surface": nombre(r"pièces?\s+([\d\s  ]+)\s?m²", texte),
            "pieces": nombre(r"(\d+)\s?pièce", texte),
            "chambres": nombre(r"(\d+)\s?chambre", texte),
            "terrain": nombre(r"([\d\s  ]+)\s?m² de terrain", texte),
            "lieu": None,  # la vraie commune est dans le titre et le lien
            "photo": photo_proche(a, BASE, 'a[href*="/annonce/"]'),
        }
    if not annonces:
        echantillon("iad-page-vide", r.text)
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
    enregistrer("IAD", list(trouvees.values()))


if __name__ == "__main__":
    main()
