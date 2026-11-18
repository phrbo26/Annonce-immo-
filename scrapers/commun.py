"""Outils partagés par tous les scripts d'agences."""
import datetime
import json
import pathlib
import re

HEADERS = {"User-Agent": "Mozilla/5.0 (recherche perso, 1 passage par jour)"}
SORTIE = pathlib.Path(__file__).resolve().parent.parent / "data" / "annonces.json"

# Codes postaux de la zone de recherche (Donzère et alentours)
CODES_POSTAUX = {"26290", "26700", "26780", "26130", "26200", "07220", "26230"}


def nombre(motif, texte):
    """Renvoie le premier nombre capturé par le motif, ou None."""
    m = re.search(motif, texte)
    if not m:
        return None
    chiffres = re.sub(r"\D", "", m.group(1).split(",")[0].split(".")[0])
    return int(chiffres) if chiffres else None


def remonter_carte(lien, marqueur="€", niveaux=8):
    """Remonte depuis un lien jusqu'au bloc HTML qui contient le marqueur (le prix)."""
    carte = lien
    for _ in range(niveaux):
        if marqueur in carte.get_text() or carte.parent is None:
            break
        carte = carte.parent
    return carte


def enregistrer(source, trouvees):
    """Remplace les annonces de `source` dans data/annonces.json sans toucher aux autres agences."""
    tout = []
    if SORTIE.exists():
        tout = json.loads(SORTIE.read_text(encoding="utf-8")).get("annonces", [])
    autres = [x for x in tout if x.get("source") != source]
    anciennes = {x["ref"]: x for x in tout if x.get("source") == source}
    aujourd_hui = datetime.date.today().isoformat()
    for x in trouvees:
        x["source"] = source
        x["vu_le"] = anciennes.get(x["ref"], {}).get("vu_le", aujourd_hui)
        x["nouveau"] = x["vu_le"] == aujourd_hui
    SORTIE.parent.mkdir(exist_ok=True)
    SORTIE.write_text(json.dumps({
        "mis_a_jour": datetime.datetime.now().isoformat(timespec="minutes"),
        "annonces": sorted(autres + trouvees, key=lambda x: x["vu_le"], reverse=True),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{source} : {len(trouvees)} annonces, {sum(x['nouveau'] for x in trouvees)} nouvelles")
