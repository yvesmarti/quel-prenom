// Mêmes règles que pipeline/normalize.py (vérifié par les tests).

const LIGATURES = { 'æ': 'ae', 'œ': 'oe' }

/** Minuscules, sans accents ni ligatures — sert uniquement à la recherche. */
export function normaliser(texte) {
  let t = texte.toLowerCase()
  for (const [lig, rempl] of Object.entries(LIGATURES)) t = t.replaceAll(lig, rempl)
  return t.normalize('NFD').replace(/\p{M}/gu, '')
}

/** Formate un effectif arrondi : « environ 1 234 ». */
export function environ(n) {
  return 'environ ' + n.toLocaleString('fr-FR')
}
