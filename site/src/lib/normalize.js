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

/** Rang ordinal en français : 1er, 2e, 3e… (renvoie le nombre et son suffixe). */
export function ordinal(n) {
  return { nombre: n.toLocaleString('fr-FR'), suffixe: n === 1 ? 'er' : 'e' }
}

/** Pourcentage lisible, y compris pour les très petites parts (« moins de 0,1 % »). */
export function pourcentage(part) {
  if (part > 0 && part < 0.001) return 'moins de 0,1 %'
  return `${(part * 100).toLocaleString('fr-FR', { maximumFractionDigits: 1 })} %`
}
