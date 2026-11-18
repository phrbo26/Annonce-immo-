"""Outils partagés par tous les scripts d'agences."""
import datetime
import json
import math
import pathlib
import re
import unicodedata
from urllib.parse import urljoin

HEADERS = {"User-Agent": "Mozilla/5.0 (recherche perso, 1 passage par jour)"}
SORTIE = pathlib.Path(__file__).resolve().parent.parent / "data" / "annonces.json"

# Codes postaux de la zone de recherche (Donzère et alentours)
CODES_POSTAUX = {"26290", "26700", "26780", "26130", "26200", "07220", "26230"}

# Point de référence pour les distances
DONZERE = (44.4428, 4.7106)

# Communes connues : nom affiché, code postal, latitude, longitude (approximatives)
COMMUNES = [
    ("Donzère", "26290", 44.4428, 4.7106),
    ("Les Granges-Gontardes", "26290", 44.4183, 4.7633),
    ("Pierrelatte", "26700", 44.3775, 4.6961),
    ("La Garde-Adhémar", "26700", 44.3967, 4.7542),
    ("Malataverne", "26780", 44.4856, 4.7533),
    ("Châteauneuf-du-Rhône", "26780", 44.4867, 4.7183),
    ("Allan", "26780", 44.4978, 4.7869),
    ("Saint-Paul-Trois-Châteaux", "26130", 44.3497, 4.7683),
    ("Clansayes", "26130", 44.3722, 4.8031),
    ("Saint-Restitut", "26130", 44.3239, 4.7914),
    ("Montélimar", "26200", 44.5581, 4.7508),
    ("Ancône", "26200", 44.5814, 4.7147),
    ("Viviers", "07220", 44.4817, 4.6889),
    ("Saint-Montan", "07220", 44.4333, 4.6408),
    ("Larnas", "07220", 44.4522, 4.6000),
    ("Roussas", "26230", 44.4333, 4.8114),
    ("Valaurie", "26230", 44.4194, 4.8139),
    ("Grignan", "26230", 44.4197, 4.9086),
    ("Réauville", "26230", 44.4447, 4.8556),
    ("Chantemerle-lès-Grignan", "26230", 44.4000, 4.8400),
    ("Espeluche", "26780", 44.5161, 4.8114),
    ("Puygiron", "26160", 44.5464, 4.8458),
    ("Montboucher-sur-Jabron", "26740", 44.5506, 4.8017),
    ("Les Tourrettes", "26740", 44.5797, 4.7378),
    ("Sauzet", "26740", 44.6033, 4.8169),
    ("Savasse", "26740", 44.6064, 4.7744),
    ("Le Teil", "07400", 44.5450, 4.6830),
    ("Rochemaure", "07400", 44.5878, 4.7019),
    ("Bourg-Saint-Andéol", "07700", 44.3728, 4.6447),
    ("Saint-Marcel-d'Ardèche", "07700", 44.3275, 4.6178),
    ("Saint-Just-d'Ardèche", "07700", 44.3006, 4.6156),
    ("Lapalud", "84840", 44.3058, 4.6889),
    ("Bollène", "84500", 44.2811, 4.7489),
    ("Mondragon", "84430", 44.2394, 4.7128),
    ("Suze-la-Rousse", "26790", 44.2886, 4.8433),
    ("Tulette", "26790", 44.2856, 4.9333),
    ("Pont-Saint-Esprit", "30130", 44.2564, 4.6489),
    ("La Baume-de-Transit", "26790", 44.3333, 4.8667),
    ("Solérieux", "26130", 44.3517, 4.8364),
    ("Montségur-sur-Lauzon", "26130", 44.3611, 4.8569),
    ("Saint-Martin-d'Ardèche", "07700", 44.3000, 4.5667),
    ("Gras", "07700", 44.4306, 4.5378),
    ("Saint-Remèze", "07700", 44.3936, 4.5050),
    ("Châteauneuf-de-Mazenc", "26220", 44.5333, 4.9500),
    ("Saint-Thomé", "07220", 44.5017, 4.6292),
]


def _simple(texte):
    """minuscules, sans accents, tirets et apostrophes remplacés par des espaces"""
    t = unicodedata.normalize("NFD", str(texte or "")).encode("ascii", "ignore").decode().lower()
    return " " + re.sub(r"[^a-z0-9]+", " ", t).strip() + " "


# du nom le plus long au plus court, pour que "saint paul trois chateaux" passe avant "paul"
_INDEX = sorted(((_simple(c[0]), c) for c in COMMUNES), key=lambda x: -len(x[0]))


def trouver_commune(*textes):
    """Cherche une commune connue dans les textes donnés, dans l'ordre (le premier texte est prioritaire)."""
    for texte in textes:
        s = _simple(texte)
        for cle, commune in _INDEX:
            if cle in s:
                return commune
    return None


def distance_km(lat, lon):
    la1, lo1 = map(math.radians, DONZERE)
    la2, lo2 = math.radians(lat), math.radians(lon)
    d = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return round(6371 * 2 * math.asin(math.sqrt(d)), 1)


TYPES = [
    ("Terrain", ("terrain a batir", "terrain constructible", "vente terrain", "sale land")),
    ("Appartement", ("appartement", "apartment", "studio", "vente appartement")),
    ("Immeuble", ("immeuble",)),
    ("Villa", ("villa",)),
    ("Mas / Ferme", (" mas ", "ferme", "bastide", "corps de ferme", "farmhouse")),
    ("Autre", ("dependance", "local commercial", "garage a vendre", "fonds de commerce", "parking")),
]


def type_bien(*textes):
    s = " ".join(_simple(t) for t in textes)
    for nom, mots in TYPES:
        if any(m in s for m in mots):
            return nom
    return "Maison"


def nombre(motif, texte):
    """Renvoie le premier nombre capturé par le motif, ou None."""
    m = re.search(motif, texte)
    if not m:
        return None
    chiffres = re.sub(r"\D", "", m.group(1).split(",")[0].split(".")[0])
    return int(chiffres) if chiffres else None


def lien_absolu(base, href):
    return urljoin(base + "/", href)


def remonter_carte(lien, marqueur="€", niveaux=8):
    """Remonte depuis un lien jusqu'au bloc HTML qui contient le marqueur (le prix)."""
    carte = lien
    for _ in range(niveaux):
        if marqueur in carte.get_text() or carte.parent is None:
            break
        carte = carte.parent
    return carte


def photo(carte, base):
    """Première vraie image de la carte (ignore logos, icônes et images vides)."""
    for img in carte.find_all("img"):
        for attr in ("data-src", "data-lazy-src", "data-original", "src", "srcset", "data-srcset"):
            v = img.get(attr)
            if not v:
                continue
            v = v.split(",")[0].split()[0]
            if v.startswith("data:") or re.search(r"logo|icon|picto|sprite|placeholder|\.svg", v, re.I):
                continue
            return lien_absolu(base, v)
    return None


def completer(x):
    """Ajoute commune, code postal, distance et type à une annonce, à partir de tout ce qu'on sait d'elle."""
    commune = trouver_commune(x.get("commune"), x.get("lien"), x.get("titre"), x.get("lieu"))
    if commune:
        nom, cp, lat, lon = commune
        x["commune"], x["cp"], x["distance_km"] = nom, cp, distance_km(lat, lon)
    else:
        x["commune"] = "Secteur non précisé"
        x.setdefault("cp", None)
        x["distance_km"] = None
    x["type"] = type_bien(x.get("titre"), x.get("lien"))
    if x.get("prix") and x.get("surface"):
        x["prix_m2"] = round(x["prix"] / x["surface"])
    return x


def enregistrer(source, trouvees, garder_inconnues=True):
    """Remplace les annonces de `source` dans data/annonces.json sans toucher aux autres agences.
    garder_inconnues=False écarte les annonces dont la commune n'est pas dans COMMUNES (trop loin)."""
    tout = []
    if SORTIE.exists():
        tout = json.loads(SORTIE.read_text(encoding="utf-8")).get("annonces", [])
    autres = [x for x in tout if x.get("source") != source]
    anciennes = {x["ref"]: x for x in tout if x.get("source") == source}
    aujourd_hui = datetime.date.today().isoformat()
    for x in trouvees:
        x["source"] = source
        completer(x)
        x["vu_le"] = anciennes.get(x["ref"], {}).get("vu_le", aujourd_hui)
        x["nouveau"] = x["vu_le"] == aujourd_hui
    if not garder_inconnues:
        trouvees = [x for x in trouvees if x["distance_km"] is not None]
    SORTIE.parent.mkdir(exist_ok=True)
    SORTIE.write_text(json.dumps({
        "mis_a_jour": datetime.datetime.now().isoformat(timespec="minutes"),
        "annonces": sorted(autres + trouvees, key=lambda x: x["vu_le"], reverse=True),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{source} : {len(trouvees)} annonces, {sum(x['nouveau'] for x in trouvees)} nouvelles")
