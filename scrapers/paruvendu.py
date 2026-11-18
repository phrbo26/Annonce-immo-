"""Annonces ParuVendu : regroupe des agences et des particuliers. Une page par commune (code INSEE) :
paruvendu.fr/immobilier/annonceimmofo/liste/listeAnnonces?tt=1&tbMai=1&codeINSEE=26116 (Donzère)
Les communes trop éloignées sont écartées par enregistrer(garder_inconnues=False)."""
import re
import time

import requests
from bs4 import BeautifulSoup

from commun import erreur, HEADERS, echantillon, enregistrer, lien_absolu, nombre, prix_isole, remonter_carte, trouver_commune

INSEE = {
    "Donzère": "26116", "Pierrelatte": "26235", "Montélimar": "26198", "Malataverne": "26171",
    "Châteauneuf-du-Rhône": "26092", "La Garde-Adhémar": "26138", "Les Granges-Gontardes": "26144",
    "Saint-Paul-Trois-Châteaux": "26324", "Viviers": "07346",
}
BASE = "https://www.paruvendu.fr"


def photo_paruvendu(carte):
    for img in carte.find_all("img"):
        src = img.get("data-src") or img.get("src") or ""
        if "media_ext" in src or (src.startswith("http") and "_static_" not in src):
            return src
    return None


def lire(code):
    url = f"{BASE}/immobilier/annonceimmofo/liste/listeAnnonces?tt=1&tbMai=1&codeINSEE={code}"
    r = requests.get(url, headers=HEADERS, timeout=30)
    if r.status_code == 404:
        return []
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    annonces = {}
    for a in soup.select('a[href*="/immobilier/vente/maison/"]'):
        m = re.search(r"/(\d{8,})[A-Z0-9]*/?$", a["href"].split("?")[0].split("#")[0])
        if not m or ("pv-" + m.group(1)) in annonces:
            continue
        carte = remonter_carte(a, niveaux=10)
        echantillon("paruvendu-carte", carte)
        texte = " ".join(carte.stripped_strings)
        texte = re.sub(r"m\s+2\b", "m²", texte)
        lieu = re.search(r"([A-ZÉÈÎa-zéèêëàâîïôûç'\- ]+) \((\d{2})\)", texte)
        commune = trouver_commune(lieu.group(1) if lieu else "", a["href"])
        img = carte.find("img")
        alt = (img.get("alt") or "").strip() if img else ""
        annonces["pv-" + m.group(1)] = {
            "ref": "pv-" + m.group(1),
            "titre": alt or "Maison à vendre",
            "lien": lien_absolu(BASE, a["href"].split("#")[0]),
            "prix": prix_isole(carte),
            "surface": nombre(r"Maison\s+([\d\s,]+)\s?m²", texte),
            "terrain": nombre(r"Terrain\s+([\d\s  ]+)\s?m²", texte),
            "pieces": nombre(r"(\d+)\s?pièces?", texte),
            "chambres": nombre(r"(\d+)\s?chambres?", texte),
            "lieu": None,
            "commune": commune[0] if commune else None,
            "photo": photo_paruvendu(carte),
        }
    if not annonces:
        echantillon("paruvendu-page-vide", r.text)
    return list(annonces.values())


def main():
    trouvees = {}
    for nom, code in INSEE.items():
        try:
            for x in lire(code):
                trouvees[x["ref"]] = x
        except Exception as e:
            erreur(nom, e)
        time.sleep(3)
    enregistrer("ParuVendu", list(trouvees.values()), garder_inconnues=False)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        from commun import signaler
        signaler("ParuVendu", "erreur", f"le script a planté : {e}"[:200])
