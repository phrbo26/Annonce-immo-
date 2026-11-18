"""Annonces Propriétés Privées : liste des maisons de la Drôme, filtrée sur nos codes postaux.
Page : proprietes-privees.com/achat/maison/drome?page=N (environ 60 maisons sur 3 pages).
Chaque annonce est un lien <a class="detail-link" href="/annonces/REF"> ; la photo est
images.proprietes-privees.com/annonce/REF/PROPRIETES-PRIVEES-REF-1.jpg"""
import re
import time

import requests
from bs4 import BeautifulSoup

from commun import CODES_POSTAUX, HEADERS, echantillon, enregistrer, nombre, trouver_commune

PAGES = ["/achat/maison/drome", "/achat/maison/ardeche"]
MAX_PAGES = 5
BASE = "https://www.proprietes-privees.com"


def lire_page(url):
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    refs, gardes = set(), []
    for a in soup.select('a[href^="/annonces/"]'):
        ref = a["href"].rstrip("/").split("/")[-1]
        if ref in refs:
            continue
        refs.add(ref)
        texte = a.get_text(" ", strip=True)
        img = a.find("img")
        alt = img.get("alt", "") if img else ""
        echantillon("proprietes_privees-carte", a)
        cp = re.search(r"\((\d{5})\)", texte)
        commune = trouver_commune(alt, texte)
        code = cp.group(1) if cp else (commune[1] if commune else None)
        if code not in CODES_POSTAUX:
            continue
        sans_m2 = re.sub(r"[\d\s  ]+€\s*/\s*m²", " ", texte)
        gardes.append({
            "ref": "pp-" + ref,
            "titre": alt or texte[:80],
            "lien": f"{BASE}/annonces/{ref}",
            "prix": nombre(r"([\d\s  ]{4,})\s?€", sans_m2),
            "surface": nombre(r"(\d+)\s?m(?:²|2)\b", alt) or nombre(r"(\d+)\s?m²", sans_m2),
            "pieces": nombre(r"(\d+)\s?pi[eè]ces?", alt) or nombre(r"(\d+)\s?p\b", texte),
            "chambres": nombre(r"(\d+)\s?ch\b", texte),
            "lieu": None,
            "commune": commune[0] if commune else None,
            "photo": f"https://images.proprietes-privees.com/annonce/{ref}/PROPRIETES-PRIVEES-{ref}-1.jpg",
        })
    if not refs:
        echantillon("proprietes_privees-page-vide", r.text)
    return refs, gardes


def main():
    trouvees, refs_vues = {}, set()
    for chemin in PAGES:
        for page in range(1, MAX_PAGES + 1):
            url = f"{BASE}{chemin}" + (f"?page={page}" if page > 1 else "")
            try:
                refs, gardes = lire_page(url)
            except Exception as e:
                print("Erreur", url, e)
                break
            if not refs or refs <= refs_vues:  # page vide ou identique à la précédente
                break
            refs_vues |= refs
            for x in gardes:
                trouvees[x["ref"]] = x
            time.sleep(3)
    print(f"Propriétés Privées : {len(refs_vues)} annonces lues sur le site")
    enregistrer("Propriétés Privées", list(trouvees.values()))


if __name__ == "__main__":
    main()
