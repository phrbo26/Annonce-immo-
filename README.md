# Annonces immo autour de Donzère

Chaque matin, un robot GitHub récupère les maisons à vendre chez plusieurs agences autour de Donzère (26290) et les range dans `data/annonces.json`. La page `index.html` les affiche, avec des filtres prix, chambres, agence et nouveautés.

## Agences couvertes

| Script | Agence | État |
| --- | --- | --- |
| `scrapers/nestenn.py` | Nestenn | page lue |
| `scrapers/orpi.py` | Orpi (Pierrelat'in, Saint James, Saint-Paul-Trois-Châteaux) | page lue |
| `scrapers/swixim.py` | Swixim Portes de Provence | page lue |
| `scrapers/iad.py` | IAD | page lue |
| `scrapers/proprietes_privees.py` | Propriétés Privées | page lue, pagination à vérifier |
| `scrapers/capifrance.py` | Capifrance | non vérifié (site bloqué à la lecture) |

À ajouter plus tard : ERA, Century 21, Stéphane Plaza, Square Habitat, Foncia. SAFTI et Vinent bloquent la lecture : alerte e-mail sur leur site.

## Réglages à faire une fois

1. **Settings → Actions → General → Workflow permissions** : « Read and write permissions ».
2. **Settings → Pages** : « Deploy from a branch », branche `main`, dossier `/ (root)`.
3. **Actions → Annonces du jour → Run workflow** pour un premier essai.
4. Sur l'iPhone, ouvrir `https://phrbo26.github.io/Annonce-immo-/` dans Safari, puis Partager → « Sur l'écran d'accueil ».

## Changer la zone

Les codes postaux gardés sont dans `scrapers/commun.py` (`CODES_POSTAUX`), et les communes de chaque agence en haut de chaque script.
