"""Sonde : télécharge les pages de recherche de nouveaux sites pour voir comment elles sont construites.
Résultat dans data/debug/sondes/ (pages compressées + un résumé). À supprimer une fois les scripts écrits."""
import gzip
import re

import requests

from commun import SORTIE

SONDES = {
    "pap": "https://www.pap.fr/annonce/vente-maisons-donzere-26290-g16796",
    "pap-pierrelatte": "https://www.pap.fr/annonce/vente-maisons-pierrelatte-26700-g16918",
    "fnaim-annonce": "https://www.fnaim.fr/annonce-immobiliere/53125502/17-acheter-maison-donzere-26290.htm",
    "fnaim-liste": "https://www.fnaim.fr/17-acheter-maison-donzere-26290.htm",
    "fnaim-liste2": "https://www.fnaim.fr/recherche/17-acheter-maison-donzere-26290.htm",
    "etreproprio-annonce": "https://www.etreproprio.com/immobilier-26375329-vente-maison-120-m-a-donzere-donzere",
    "etreproprio-liste": "https://www.etreproprio.com/annonces/thf.r-26.odd.g-donzere",
    "efficity": "https://www.efficity.com/achat-immobilier/maison_donzere_26290/",
    "laforet-ville": "https://www.laforet.com/ville/achat-maison-donzere-26290",
    "lesiteimmo": "https://www.lesiteimmo.com/acheter/maison/donzere-26290",
    "bienici-suggest": "https://res.bienici.com/suggest.json?q=donzere",
    "superimmo": "https://www.superimmo.com/achat/maison/rhone-alpes/drome/donzere",
    "greenacres": "https://www.green-acres.fr/maison-a-vendre/donzere",
    "ouestfrance": "https://www.ouestfrance-immo.com/acheter/maison/donzere-26-26290/",
    "paruvendu": "https://www.paruvendu.fr/immobilier/annonceimmofo/liste/listeAnnonces?tt=1&tbMai=1&codeINSEE=26116",
}
NAVIGATEUR = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
              "(KHTML, like Gecko) Version/17.0 Safari/605.1.15", "Accept-Language": "fr-FR,fr;q=0.9"}

dossier = SORTIE.parent / "debug" / "sondes"
dossier.mkdir(parents=True, exist_ok=True)
resume = []
for nom, url in SONDES.items():
    try:
        r = requests.get(url, headers=NAVIGATEUR, timeout=30)
        euros = len(re.findall(r"\d[\d\s  .]{2,}\s?(?:€|&euro;)", r.text))
        ligne = f"{nom}: {r.status_code} {len(r.text)} octets, {euros} prix, finale={r.url}"
        (dossier / f"{nom}.html.gz").write_bytes(gzip.compress(r.text[:800000].encode("utf-8")))
    except Exception as e:
        ligne = f"{nom}: ERREUR {e}"
    print(ligne)
    resume.append(ligne)
(dossier / "resume.txt").write_text("\n".join(resume), encoding="utf-8")
