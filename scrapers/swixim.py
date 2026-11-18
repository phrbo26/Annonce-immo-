"""Annonces Swixim Portes de Provence (Pierrelatte) : une seule page d'agence.
Les liens contiennent tout : /our-properties/ref-87525969/sale-house-donzere-7-rooms-4-bedrooms-26290/"""
import re

import requests
from bs4 import BeautifulSoup

from commun import CODES_POSTAUX, HEADERS, enregistrer

URL = "https://www.swixim.com/en/agencies/details/20/swixim-portes-de-provence/"
BASE = "https://www.swixim.com"
TYPES = {"house", "villa", "mas", "bastide", "farmhouse"}  # ajoute "apartment" ou "land" si besoin
MOTIF = re.compile(r"/ref-(\d+)/sale-([a-z]+)-(.+?)-(\d+)-rooms?(?:-(\d+)-bedrooms?)?-(\d{5})/")


def main():
    r = requests.get(URL, headers=HEADERS, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    annonces = {}
    for a in soup.select('a[href*="/our-properties/ref-"]'):
        texte = a.get_text(" ", strip=True)
        if "Sold" in texte or "rented" in texte or "Vendu" in texte:
            continue
        m = MOTIF.search(a["href"])
        if not m:
            continue
        ref, type_bien, ville, pieces, chambres, cp = m.groups()
        if cp not in CODES_POSTAUX or type_bien not in TYPES:
            continue
        prix = re.search(r"([\d,\s  ]+)\s?€", texte)
        surface = re.search(r"([\d.]+)\s?m²", texte)
        annonces[ref] = {
            "ref": "swixim-" + ref,
            "titre": a.get("title") or texte[:80],
            "lien": a["href"] if a["href"].startswith("http") else BASE + a["href"],
            "prix": int(re.sub(r"\D", "", prix.group(1))) if prix else None,
            "surface": round(float(surface.group(1))) if surface else None,
            "pieces": int(pieces),
            "chambres": int(chambres) if chambres else None,
            "lieu": f"{cp} {ville.replace('-', ' ').title()}",
        }
    enregistrer("Swixim", list(annonces.values()))


if __name__ == "__main__":
    main()
