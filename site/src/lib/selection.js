// Mémoire du visiteur : préférences, prénoms gardés, à revoir et écartés.
// Tout reste dans le navigateur (localStorage) ; rien n'est envoyé. Fonctions pures, testables sans navigateur.
import { preferencesVides } from './suggestions.js'

export const CLE_STOCKAGE = 'prenoscope.selection.v1'
const MAX_PARTAGE = 200

export function selectionVide() {
  return {
    version: 1,
    questionnaire: 'a_faire', // a_faire | passe | fait
    prefs: preferencesVides(),
    gardes: [],
    plusTard: [],
    ecartes: [],
    historique: [], // [{ id, action }] pour annuler le dernier geste
  }
}

const listeIds = (x) => (Array.isArray(x) ? x.filter((i) => typeof i === 'string').slice(0, 5000) : [])

/** Reconstruit une sélection valide à partir de données quelconques (stockage ancien, fichier importé). */
export function nettoyer(brut) {
  const base = selectionVide()
  if (!brut || typeof brut !== 'object') return base
  const prefs = { ...base.prefs }
  for (const [cle, defaut] of Object.entries(base.prefs)) {
    const v = brut.prefs?.[cle]
    if (Array.isArray(defaut)) prefs[cle] = listeIds(v)
    else if (typeof v === 'string') prefs[cle] = v
  }
  return {
    version: 1,
    questionnaire: ['a_faire', 'passe', 'fait'].includes(brut.questionnaire) ? brut.questionnaire : 'a_faire',
    prefs,
    gardes: listeIds(brut.gardes),
    plusTard: listeIds(brut.plusTard),
    ecartes: listeIds(brut.ecartes),
    historique: Array.isArray(brut.historique)
      ? brut.historique.filter((h) => typeof h?.id === 'string' && ['garder', 'ecarter', 'plusTard'].includes(h.action)).slice(-50)
      : [],
  }
}

export function lire(stockage = globalThis.localStorage) {
  try {
    return nettoyer(JSON.parse(stockage.getItem(CLE_STOCKAGE)))
  } catch {
    return selectionVide() // stockage absent, bloqué ou corrompu : le site fonctionne sans mémoire
  }
}

export function ecrire(selection, stockage = globalThis.localStorage) {
  try {
    stockage.setItem(CLE_STOCKAGE, JSON.stringify(selection))
    return true
  } catch {
    return false
  }
}

// --- Gestes ------------------------------------------------------------------------------------------

const LISTE_DE = { garder: 'gardes', ecarter: 'ecartes', plusTard: 'plusTard' }

function retirerPartout(sel, id) {
  for (const l of Object.values(LISTE_DE)) sel[l] = sel[l].filter((x) => x !== id)
}

/** Range un prénom dans une liste (le retire des autres) et garde la trace pour pouvoir annuler. */
export function classer(sel, id, action) {
  retirerPartout(sel, id)
  sel[LISTE_DE[action]].unshift(id)
  sel.historique = [...sel.historique, { id, action }].slice(-50)
}

/** Sort un prénom de toutes les listes (il pourra de nouveau être proposé). */
export function oublier(sel, id) {
  retirerPartout(sel, id)
  sel.historique = sel.historique.filter((h) => h.id !== id)
}

/** Annule le dernier geste ; renvoie l'identifiant concerné (ou null). */
export function annuler(sel) {
  const dernier = sel.historique.at(-1)
  if (!dernier) return null
  sel.historique = sel.historique.slice(0, -1)
  retirerPartout(sel, dernier.id)
  return dernier.id
}

// --- Partage ------------------------------------------------------------------------------------------

/** Liste d'identifiants → texte de lien (#/liste?g=lea,jade). Les identifiants sont des graphies Insee en minuscules. */
export function encoderPartage(ids) {
  return ids.slice(0, MAX_PARTAGE).map(encodeURIComponent).join(',')
}

export function decoderPartage(texte) {
  if (!texte) return []
  const ids = String(texte).split(',').map((s) => {
    try { return decodeURIComponent(s).trim().toLowerCase() } catch { return '' }
  })
  return [...new Set(ids.filter((s) => s && s.length <= 40))].slice(0, MAX_PARTAGE)
}

export function exporterJson(sel) {
  return JSON.stringify({ ...sel, historique: [] }, null, 2)
}

export function importerJson(texte) {
  try {
    const brut = JSON.parse(texte)
    if (!brut || typeof brut !== 'object' || !Array.isArray(brut.gardes)) return null
    return nettoyer(brut)
  } catch {
    return null
  }
}
