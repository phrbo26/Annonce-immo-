"""Annonces Capifrance (NON VÉRIFIÉ : le site a refusé la lecture pendant la préparation).
Pages par commune : capifrance.fr/residentiel/acheter/recherche/pierrelatte/maison
Si le site bloque GitHub, le script affiche 403 et n'efface rien : créer une alerte e-mail à la place."""
import re
import time

import requests
from bs4 import BeautifulSoup

from commun import HEADERS, enregistrer, nombre, remonter_carte

COMMUNES = [
    "donzere", "pierrelatte", "la-garde-adhemar", "saint-paul-trois-chateaux",
    "malataverne", "chateauneuf-du-rhone", "montelimar", "viviers",
]
BASE = "https://www.capifrance.fr"


def lire_commune(commune):
    r = requests.get(f"{BASE}/residentiel/acheter/recherche/{commune}/maison", headers=HEADERS, timeout=30)
    if r.status_code in (403, 404):
        print("Capifrance", commune, "->", r.status_code)
        return None
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    annonces = {}
    for a in soup.select('a[href*="/residentiel/vente/"]'):
        lien = a["href"] if a["href"].startswith("http") else BASE + a["href"]
        m = re.search(r"/(\d+)-vente-", lien)
        if not m:
            continue
        ref = "capifrance-" + m.group(1)
        if ref in annonces:
            continue
        texte = remonter_carte(a).get_text(" ", strip=True)
        if "Sous compromis" in texte:
            continue
        surfaces = re.findall(r"([\d\s  ]+)m²", texte)
        ville = re.search(r"([A-ZÉÈ\-' ]+) \(\d{2}\)", texte)
        annonces[ref] = {
            "ref": ref,
            "titre": texte[:80],
            "lien": lien,
            "prix": nombre(r"([\d\s  ]+)\s?€", texte),
            "surface": int(re.sub(r"\D", "", surfaces[0])) if surfaces else None,
            "terrain": int(re.sub(r"\D", "", surfaces[1])) if len(surfaces) > 1 else None,
            "pieces": nombre(r"(\d+)p\b", texte),
            "chambres": nombre(r"(\d+)ch\b", texte),
            "lieu": ville.group(1).strip().title() if ville else commune.title(),
        }
    return list(annonces.values())


def main():
    trouvees, bloque = {}, False
    for commune in COMMUNES:
        try:
            lot = lire_commune(commune)
        except Exception as e:
            print("Erreur", commune, e)
            lot = None
        if lot is None:
            bloque = True
            continue
        for x in lot:
            trouvees[x["ref"]] = x
        time.sleep(3)
    if bloque and not trouvees:
        print("Capifrance inaccessible : annonces précédentes conservées")
        return
    enregistrer("Capifrance", list(trouvees.values()))


if __name__ == "__main__":
    main()
