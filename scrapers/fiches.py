"""Complète les annonces auxquelles il manque la surface du terrain, en ouvrant leur page détaillée.
Les résultats sont gardés dans data/fiches.json : une page n'est ouverte qu'une fois (nouvel essai après 7 jours
si rien n'avait été trouvé). Au plus MAX_PAGES pages par passage, pour rester discret avec les sites.
À lancer après les scripts d'agences et avant marche.js (le terrain sert à l'estimation)."""
import datetime
import json
import time
from collections import Counter
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from commun import HEADERS, SORTIE, terrain_texte

CACHE = SORTIE.parent / "fiches.json"
MAX_PAGES = 300
PAUSE = 2
REESSAI_JOURS = 7
TYPES_AVEC_TERRAIN = {"Maison", "Villa", "Mas / Ferme", "Autre"}


def terrain_page(html):
    soup = BeautifulSoup(html, "html.parser")
    for el in soup(["script", "style", "noscript", "header", "footer", "nav"]):
        el.decompose()
    # les blocs « biens similaires » parlent d'autres maisons : on les retire quand on les reconnaît
    for el in soup.find_all(True, class_=lambda c: c and any(k in " ".join(c).lower() for k in ("similar", "similaire", "suggest", "carousel-biens"))):
        el.decompose()
    return terrain_texte(soup.get_text(" ", strip=True))


def main():
    donnees = json.loads(SORTIE.read_text(encoding="utf-8"))
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    aujourd_hui = datetime.date.today()
    a_ouvrir, repris = [], 0
    for a in donnees["annonces"]:
        if a.get("terrain") or a.get("type") not in TYPES_AVEC_TERRAIN or not a.get("lien"):
            continue
        c = cache.get(a["ref"])
        if c and c.get("terrain"):
            a["terrain"] = c["terrain"]
            repris += 1
        elif not c or (aujourd_hui - datetime.date.fromisoformat(c["vu"])).days >= REESSAI_JOURS:
            a_ouvrir.append(a)

    refus, ouvertes, trouves = Counter(), 0, 0
    for a in a_ouvrir[:MAX_PAGES]:
        site = urlparse(a["lien"]).netloc
        if refus[site] >= 2:  # le site nous refuse : inutile d'insister aujourd'hui
            continue
        try:
            r = requests.get(a["lien"], headers=HEADERS, timeout=30)
            ouvertes += 1
            if r.status_code in (403, 429):
                refus[site] += 1
                continue
            if r.status_code in (404, 410):
                cache[a["ref"]] = {"terrain": None, "vu": aujourd_hui.isoformat(), "statut": r.status_code}
                continue
            r.raise_for_status()
            t = terrain_page(r.text)
            cache[a["ref"]] = {"terrain": t, "vu": aujourd_hui.isoformat()}
            if t:
                a["terrain"] = t
                trouves += 1
        except Exception as e:
            print("Fiche", a["ref"], e)
        time.sleep(PAUSE)

    # on oublie les annonces disparues depuis plus de 60 jours
    refs = {a["ref"] for a in donnees["annonces"]}
    cache = {k: v for k, v in cache.items()
             if k in refs or (aujourd_hui - datetime.date.fromisoformat(v["vu"])).days < 60}
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    SORTIE.write_text(json.dumps(donnees, ensure_ascii=False, indent=2), encoding="utf-8")
    reste = max(0, len(a_ouvrir) - MAX_PAGES)
    print(f"Fiches : {repris} terrains repris de la mémoire, {ouvertes} pages ouvertes, {trouves} terrains trouvés"
          + (f", {reste} à faire aux prochains passages" if reste else "")
          + (f", refus de {', '.join(refus)}" if refus else ""))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("Fiches : erreur", e)
