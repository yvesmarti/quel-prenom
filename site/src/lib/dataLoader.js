// Chargement des fichiers JSON générés par le pipeline (site/public/data/).
// Chaque fichier n'est téléchargé qu'une fois par visite (cache en mémoire).

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
  }))
}

let indexDecode = null
export async function chargerIndex() {
  if (!indexDecode) indexDecode = decoderIndex(await charger('index.v1.json'))
  return indexDecode
}

export const chargerMeta = () => charger('meta.json')

/** Séries nationales { F: [[annee, valeur, rang], …], M: […] } d'un prénom. */
export async function chargerSeries(prenom) {
  const lot = await charger(`prenoms/${prenom.lot}.json`)
  return lot.prenoms[prenom.id] || {}
}
