"""Annonces du portail Le Site Immo : il regroupe de nombreuses agences locales (Saint Martin, K2, Miranda,
Faure, Sud Immo, CTI Provence, SAFTI…). Les données sont lues dans le bloc JSON-LD (schema.org) de la page :
lesiteimmo.com/acheter/maison/donzere-26290?page=N
Les agences déjà suivies directement par un autre script sont ignorées, pour éviter les doublons."""
import json
import re
import time

import requests
from bs4 import BeautifulSoup

from commun import erreur, HEADERS, echantillon, enregistrer, trouver_commune

PAGES = [
    "donzere-26290", "pierrelatte-26700", "montelimar-26200", "malataverne-26780", "chateauneuf-du-rhone-26780",
    "la-garde-adhemar-26700", "les-granges-gontardes-26290", "saint-paul-trois-chateaux-26130", "viviers-07220",
]
MAX_PAGES = 3
BASE = "https://www.lesiteimmo.com"
DEJA_SUIVIES = ("iad", "propriétés privées", "proprietes privees", "orpi", "saint james", "nestenn", "century 21",
                "era ", "square habitat", "swixim")
TYPES = {"House": "Maison", "SingleFamilyResidence": "Maison", "Apartment": "Appartement"}


def annonces_jsonld(html):
    soup = BeautifulSoup(html, "html.parser")
    for bloc in soup.find_all("script", type="application/ld+json"):
        try:
            d = json.loads(bloc.string or "")
        except ValueError:
            continue
        liste = (d.get("mainEntity") or {}).get("itemListElement") if isinstance(d, dict) else None
        if liste:
            return [e.get("item", {}) for e in liste]
    return []


def lire(page, n):
    r = requests.get(f"{BASE}/acheter/maison/{page}" + (f"?page={n}" if n > 1 else ""), headers=HEADERS, timeout=30)
    if r.status_code == 404:
        return set(), []
    r.raise_for_status()
    items = annonces_jsonld(r.text)
    if not items:
        echantillon("lesiteimmo-page-vide", r.text)
    annonces, refs = [], {i.get("url") for i in items}
    for i in items:
        offre = i.get("offers") or {}
        bien = offre.get("itemOffered") or {}
        vendeur = (offre.get("seller") or {}).get("name") or ""
        if any(nom in vendeur.lower() + " " for nom in DEJA_SUIVIES):
            continue
        m = re.search(r"/(\d+)/?$", i.get("url", ""))
        if not m:
            continue
        adresse = bien.get("address") or {}
        commune = trouver_commune(adresse.get("addressLocality"), i.get("url"))
        surface = bien.get("floorSize")
        images = i.get("image") or []
        annonces.append({
            "ref": "lsi-" + m.group(1),
            "titre": i.get("name") or bien.get("name") or "Maison",
            "lien": i.get("url"),
            "prix": offre.get("price"),
            "surface": round((surface or {}).get("value")) if isinstance(surface, dict) and surface.get("value") else None,
            "pieces": bien.get("numberOfRooms"),
            "chambres": bien.get("numberOfBedrooms"),
            "lieu": None,
            "commune": commune[0] if commune else adresse.get("addressLocality"),
            "type": TYPES.get(bien.get("@type"), "Maison"),
            "agence": vendeur.title() if vendeur.islower() else vendeur,
            "photo": images[0] if isinstance(images, list) and images else (images or None),
        })
    return refs, annonces


def main():
    trouvees, vues = {}, set()
    for page in PAGES:
        for n in range(1, MAX_PAGES + 1):
            try:
                refs, lot = lire(page, n)
            except Exception as e:
                erreur(page, n, e)
                break
            for x in lot:
                trouvees[x["ref"]] = x
            time.sleep(3)
            if not refs or refs <= vues:  # page vide ou déjà vue
                break
            vues |= refs
    enregistrer("Le Site Immo", list(trouvees.values()), garder_inconnues=False)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        from commun import signaler
        signaler("Le Site Immo", "erreur", f"le script a planté : {e}"[:200])
