"""Annonces Orpi : une page par commune, ex. orpi.com/annonces-immobilieres-donzere/vente-maison/
Couvre Orpi Pierrelat'in, Agence Saint James (Montélimar) et Orpi Saint-Paul-Trois-Châteaux."""
import re
import time

import requests
from bs4 import BeautifulSoup

from commun import HEADERS, enregistrer, lien_absolu, nombre, echantillon, photo, remonter_carte

COMMUNES = [
    "donzere", "les-granges-gontardes", "pierrelatte", "la-garde-adhemar",
    "malataverne", "chateauneuf-du-rhone", "saint-paul-trois-chateaux",
    "montelimar", "viviers", "saint-montan", "roussas", "valaurie",
]
BASE = "https://www.orpi.com"


def lire_commune(commune):
    r = requests.get(f"{BASE}/annonces-immobilieres-{commune}/vente-maison/", headers=HEADERS, timeout=30)
    if r.status_code == 404:
        return []
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    annonces = {}
    for a in soup.select('a[href*="annonce-vente"]'):
        lien = lien_absolu(BASE, a["href"])
        # l'identifiant est l'UUID à la fin de l'adresse
        m = re.search(r"([0-9a-f]{8}-[0-9a-f-]{27})/?$", lien)
        ref = "orpi-" + (m.group(1) if m else lien.rstrip("/").split("/")[-1])
        if ref in annonces:
            continue
        carte = remonter_carte(a)
        echantillon("orpi-carte", carte)
        texte = carte.get_text(" ", strip=True)
        titre = a.get_text(" ", strip=True)
        annonces[ref] = {
            "ref": ref,
            "titre": titre,
            "lien": lien,
            "prix": nombre(r"([\d\s  ]+)\s?€(?!\s?/)", texte),
            "surface": nombre(r"([\d,]+)\s?m\s?2", titre),
            "pieces": nombre(r"(\d+)\s?pièce", titre),
            "chambres": None,
            "lieu": None,  # la vraie commune est lue dans le lien
            "photo": photo(carte, BASE),
        }
    if not annonces:
        echantillon("orpi-page-vide", r.text)
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
    enregistrer("Orpi", list(trouvees.values()), garder_inconnues=False)


if __name__ == "__main__":
    main()
