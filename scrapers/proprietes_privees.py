"""Annonces Propriétés Privées : liste des maisons de la Drôme, filtrée sur nos codes postaux.
Page : proprietes-privees.com/achat/maison/drome (environ 60 maisons sur 3 pages).
À vérifier au premier lancement : le paramètre de pagination (?page=2) est supposé."""
import re
import time

import requests
from bs4 import BeautifulSoup

from commun import CODES_POSTAUX, HEADERS, enregistrer

PAGES = ["/achat/maison/drome"]  # ajouter "/achat/maison/ardeche" pour Viviers, Saint-Montan
MAX_PAGES = 4
BASE = "https://www.proprietes-privees.com"

FICHE = re.compile(
    r"Ref\. (\w+) ([A-ZÉÈÎ'\- ]+) \((\d{5})\) ([\d\s  ]+) €"
    r".*?(\d+) m² (\d+) p(?: (\d+) ch)? Découvrir ce bien", re.S)


def lire_page(url):
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    texte = BeautifulSoup(r.text, "html.parser").get_text(" ", strip=True)
    tous, gardes = FICHE.findall(texte), []
    for ref, ville, cp, prix, surface, pieces, chambres in tous:
        if cp not in CODES_POSTAUX:
            continue
        gardes.append({
            "ref": "pp-" + ref,
            "titre": f"Maison {surface} m² à {ville.title()}",
            "lien": f"{BASE}/annonces/{ref}",
            "prix": int(re.sub(r"\D", "", prix)),
            "surface": int(surface),
            "pieces": int(pieces),
            "chambres": int(chambres) if chambres else None,
            "lieu": f"{cp} {ville.title()}",
        })
    return tous, gardes


def main():
    trouvees, refs_vues = {}, set()
    for chemin in PAGES:
        for page in range(1, MAX_PAGES + 1):
            url = f"{BASE}{chemin}" + (f"?page={page}" if page > 1 else "")
            try:
                tous, gardes = lire_page(url)
            except Exception as e:
                print("Erreur", url, e)
                break
            refs = {t[0] for t in tous}
            if not refs or refs <= refs_vues:  # page vide ou identique à la précédente
                break
            refs_vues |= refs
            for x in gardes:
                trouvees[x["ref"]] = x
            time.sleep(3)
    enregistrer("Propriétés Privées", list(trouvees.values()))


if __name__ == "__main__":
    main()
