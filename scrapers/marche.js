/* Compare chaque annonce au prix du marché calculé par l'Estimateur DVF (github.com/phrbo26/Estimateur-Immo).
   Utilise le même algorithme (estimation.js) et les mêmes ventes notariées que l'estimateur publié.
   Usage : node scrapers/marche.js [data/annonces.json] [url de l'estimateur]
   Ajoute à chaque annonce un champ "marche" ; n'efface rien si l'estimateur est injoignable. */
"use strict";
const fs = require("fs"), os = require("os"), path = require("path");

const FICHIER = process.argv[2] || path.join(__dirname, "..", "data", "annonces.json");
const ESTIMATEUR = (process.argv[3] || "https://phrbo26.github.io/Estimateur-Immo/").replace(/\/?$/, "/");
// Les annonces affichent un prix « frais d'agence inclus » ; DVF enregistre le prix payé au vendeur.
const FRAIS_AGENCE = 0.05;
// En dessous de ce score de l'estimateur (sur 100), on n'affiche pas de verdict tranché.
const SEUIL_FIABILITE = 20;
const TYPES = { Maison: "Maison", Villa: "Maison", "Mas / Ferme": "Maison", Appartement: "Appartement" };

async function lire(url, format = "json") {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${r.status} sur ${url}`);
  return format === "json" ? r.json() : r.text();
}

/* Où tombe le prix demandé parmi les ventes réelles comparables (frais d'agence ajoutés) :
   sous le quart le moins cher = bonne affaire ; dans la fourchette = marché ; au-dessus = cher. */
function verdict(prix, bas, haut, ventes, fiabilite) {
  if (ventes < 8 || fiabilite < SEUIL_FIABILITE) return "incertain";
  if (prix <= bas) return "bonne-affaire";
  if (prix <= haut) return "marche";
  if (prix <= haut * 1.15) return "un-peu-cher";
  return "trop-cher";
}

function lienEstimateur(a, type) {
  const p = new URLSearchParams({ adresse: `${a.commune} (centre)`, lat: a.lat.toFixed(6), lon: a.lon.toFixed(6),
    insee: a.cp || "26000", type, surface: a.surface, etat: "bon" });
  if (a.pieces) p.set("pieces", a.pieces);
  if (a.terrain) p.set("terrain", a.terrain);
  return ESTIMATEUR + "?" + p;
}

async function main() {
  const donnees = JSON.parse(fs.readFileSync(FICHIER, "utf8"));
  let E, indices, meta;
  try {
    const code = await lire(ESTIMATEUR + "estimation.js", "text");
    const tmp = path.join(os.tmpdir(), "estimation-dvf.js");
    fs.writeFileSync(tmp, code);
    E = require(tmp);
    [indices, meta] = await Promise.all([lire(ESTIMATEUR + "data/indices.json"), lire(ESTIMATEUR + "data/meta.json").catch(() => null)]);
  } catch (e) {
    console.log("Marché : estimateur injoignable, estimations précédentes conservées :", e.message);
    donnees.marche = { ...(donnees.marche || {}), statut: "erreur", message: "estimateur injoignable" };
    fs.writeFileSync(FICHIER, JSON.stringify(donnees, null, 2));
    return;
  }

  const tuiles = new Map();
  const tuile = cle => {
    if (!tuiles.has(cle)) tuiles.set(cle, lire(`${ESTIMATEUR}data/tuiles/${cle}.json`).then(E.lireTuile).catch(() => []));
    return tuiles.get(cle);
  };
  const ventesParCommune = new Map();
  const ventesAutour = a => {
    const cle = `${a.lat},${a.lon}`;
    if (!ventesParCommune.has(cle)) ventesParCommune.set(cle, Promise.all(E.tuilesAutour(a.lat, a.lon).map(tuile)).then(l => l.flat()));
    return ventesParCommune.get(cle);
  };

  let faites = 0, ignorees = 0;
  const aujourdHui = new Date();
  for (const a of donnees.annonces) {
    const type = TYPES[a.type];
    if (!type || !a.prix || !a.surface || a.surface < 9 || a.lat == null || a.lon == null) { delete a.marche; ignorees++; continue; }
    const bien = { lat: a.lat, lon: a.lon, type, surface: a.surface, pieces: a.pieces || null, etat: "bon", dpe: "",
      etage: null, ascenseur: false, balcon: 0, terrasse: 0, terrain: a.terrain || 0 };
    const ventes = await ventesAutour(a);
    let r = E.estimer(ventes, bien, aujourdHui, { indices });
    if (!r.ok && bien.pieces) r = E.estimer(ventes, { ...bien, pieces: null }, aujourdHui, { indices });  // sans le nombre de pièces
    if (!r.ok) { delete a.marche; ignorees++; continue; }
    const reference = r.estimation.median * (1 + FRAIS_AGENCE);
    const ecart = a.prix / reference - 1;
    a.marche = {
      estimation: r.estimation.median, bas: r.estimation.bas, haut: r.estimation.haut,
      prix_m2: Math.round(r.prixM2.median), avec_frais: Math.round(reference / 1000) * 1000,
      ecart: Math.round(ecart * 1000) / 1000,
      verdict: verdict(a.prix, r.estimation.bas * (1 + FRAIS_AGENCE), r.estimation.haut * (1 + FRAIS_AGENCE), r.comparables.length, r.fiabilite.score),
      fiabilite: r.fiabilite.score, niveau: r.fiabilite.niveau, ventes: r.comparables.length, rayon: r.rayon,
      lien: lienEstimateur(a, type),
    };
    faites++;
  }
  donnees.marche = {
    statut: "ok", estimees: faites, ignorees, frais_agence: FRAIS_AGENCE,
    derniere_vente: meta?.derniere_vente || null, calcule: new Date().toISOString().slice(0, 16) + "+00:00",
  };
  fs.writeFileSync(FICHIER, JSON.stringify(donnees, null, 2));
  console.log(`Marché : ${faites} annonces comparées au marché, ${ignorees} sans estimation possible`);
}

main().catch(e => { console.log("Marché : erreur", e.message); process.exitCode = 0; });
