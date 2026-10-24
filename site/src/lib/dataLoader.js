// Chargement des fichiers JSON générés par le pipeline (site/public/data/).
// Chaque fichier n'est téléchargé qu'une fois par visite (cache en mémoire).

import { decoderProfils } from './suggestions.js'

const BASE = import.meta.env.BASE_URL + 'data/'
const cache = new Map()

function charger(chemin) {
  if (!cache.has(chemin)) {
    const promesse = fetch(BASE + chemin).then((r) => {
      if (!r.ok) throw new Error(`Fichier introuvable : ${chemin} (${r.status})`)
      return r.json()
    })
    promesse.catch(() => cache.delete(chemin)) // permet de réessayer après une erreur réseau
    cache.set(chemin, promesse)
  }
  return cache.get(chemin)
}

/** Transforme l'index compact (colonnes + lignes) en objets lisibles. */
export function decoderIndex(json) {
  const col = Object.fromEntries(json.colonnes.map((nom, i) => [nom, i]))
  return json.lignes.map((l) => ({
    id: l[col.id],
    affichage: l[col.affichage],
    norm: l[col.norm],
    sexe: l[col.sexe],
    totalF: l[col.total_f],
    totalM: l[col.total_m],
    total: l[col.total_f] + l[col.total_m],
    premiereAnnee: l[col.premiere_annee],
    derniereAnnee: l[col.derniere_annee],
    lettres: l[col.lettres],
    accent: l[col.accent] === 1,
    compose: l[col.compose] === 1,
    lot: l[col.lot],
    // Qualité de la fiche : c = complète, p = partielle, m = minimale (absent des anciens index : m).
    qualite: col.qualite != null ? l[col.qualite] : 'm',
  }))
}

/**
 * Clé de lot : premières lettres a–z de la forme normalisée (même règle que pipeline/normalize.py).
 * 2 lettres pour les séries, 3 pour les données géographiques.
 */
export function cleLot(norm, longueur = 2) {
  return (norm.match(/[a-z]/g) || []).slice(0, longueur).join('') || '_'
}

let indexDecode = null
let indexParId = null
export async function chargerIndex() {
  if (!indexDecode) indexDecode = decoderIndex(await charger('index.v1.json'))
  return indexDecode
}
/** Map id → prénom de l'index (pour afficher les noms des classements et tendances). */
export async function chargerIndexParId() {
  if (!indexParId) indexParId = new Map((await chargerIndex()).map((p) => [p.id, p]))
  return indexParId
}

export const chargerMeta = () => charger('meta.json')
export const chargerTendances = () => charger('tendances.json')
export const chargerCouverture = () => charger('couverture.json')
export const chargerClassementAnnee = (annee) => charger(`classements/france/${annee}.json`)
export const chargerClassementDecennies = () => charger('classements/france-decennies.json')
export const chargerClassementZone = (niveau, code) => charger(`classements/zones/${niveau}-${code}.json`)
export const chargerZones = () => charger('geo/zones.json')
export const chargerTotauxGeo = () => charger('geo/totaux.json')
export const chargerFondDeCarte = (niveau) => charger(niveau === 'REG' ? 'geo/regions.json' : 'geo/departements.json')

/** Séries nationales { F: [[annee, valeur, rang], …], M: […], tendances?, vagues? } d'un prénom. */
export async function chargerSeries(prenom) {
  const lot = await charger(`prenoms/${prenom.lot}.json`)
  return lot.prenoms[prenom.id] || {}
}

/** Effectifs par zone et décennie { F: { REG: [[code, decennie, valeur]…], DEP: […] }, M: … }. */
export async function chargerGeoPrenom(prenom) {
  try {
    const lot = await charger(`geo/prenoms/g_${cleLot(prenom.norm, 3)}.json`)
    return lot.prenoms[prenom.id] || {}
  } catch {
    return {} // prénom absent des niveaux régional et départemental : pas de fichier
  }
}

/** Fichier optionnel : renvoie {} si le prénom n'a pas d'entrée (ou si le lot n'existe pas). */
async function entreeOptionnelle(chemin, id) {
  try {
    return (await charger(chemin)).prenoms[id] || {}
  } catch {
    return {}
  }
}

/** Enrichissement Wikidata (CC0) : éléments, langues d'usage, variantes, personnalités. */
export const chargerEncyclo = (prenom) => entreeOptionnelle(`encyclo/${prenom.lot}.json`, prenom.id)

/** Enrichissement Wiktionnaire (CC BY-SA 4.0) : étymologie, origine, prononciation, variantes. */
export const chargerWiktionnaire = (prenom) => entreeOptionnelle(`wiktionnaire/${prenom.lot}.json`, prenom.id)

/** Profils compacts des prénoms suggérables (voir pipeline/export_json.py, exporter_profils). */
let profilsDecodes = null
export async function chargerProfils() {
  if (!profilsDecodes) profilsDecodes = decoderProfils(await charger('profils.v1.json'))
  return profilsDecodes
}
