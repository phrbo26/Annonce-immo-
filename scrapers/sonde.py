"""Sonde : télécharge les pages de recherche de nouvelles agences pour voir comment elles sont construites.
Résultat dans data/debug/sondes/ (une page par agence + un résumé). À supprimer une fois les scripts écrits."""
import pathlib
import re

import requests

from commun import HEADERS, SORTIE

SONDES = {
    "era": "https://www.erafrance.com/acheter/Pierrelatte-c36080?display=list&page=1",
    "era-donzere": "https://www.erafrance.com/acheter/Donzere-c36065?display=list&page=1",
    "century21": "https://www.century21.fr/annonces/achat-maison/v-montelimar/",
    "century21-donzere": "https://www.century21.fr/annonces/achat-maison/v-donzere/",
    "stephaneplaza": "https://www.stephaneplazaimmobilier.com/acheter/ville/montelimar_26198/maison/",
    "squarehabitat": "https://www.squarehabitat.fr/acheter-maison-montelimar-26200.aspx",
    "foncia": "https://fr.foncia.com/achat/montelimar-26200/maison",
    "safti": "https://www.safti.fr/annonces/achat/maison/donzere-26290",
    "safti-acheter": "https://www.safti.fr/acheter",
    "laforet": "https://www.laforet.com/acheter/rechercher?filter%5Bcities%5D%5B%5D=26198&filter%5Btypes%5D%5B%5D=house",
    "guyhoquet": "https://www.guy-hoquet.com/biens/result#1&p=1&f10=1&f20=26_c2_26198",
}

dossier = SORTIE.parent / "debug" / "sondes"
dossier.mkdir(parents=True, exist_ok=True)
resume = []
for nom, url in SONDES.items():
    try:
        r = requests.get(url, headers={**HEADERS, "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                                       "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
                                       "Accept-Language": "fr-FR,fr;q=0.9"}, timeout=30)
        euros = len(re.findall(r"\d[\d\s  .]{2,}\s?€", r.text))
        ligne = f"{nom}: {r.status_code} {len(r.text)} octets, {euros} prix, finale={r.url}"
        (dossier / f"{nom}.html").write_text(r.text[:600000], encoding="utf-8")
    except Exception as e:
        ligne = f"{nom}: ERREUR {e}"
    print(ligne)
    resume.append(ligne)
(dossier / "resume.txt").write_text("\n".join(resume), encoding="utf-8")
