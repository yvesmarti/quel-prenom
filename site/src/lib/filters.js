import { normaliser } from './normalize.js'

export const CRITERES_VIDES = {
  texte: '',
  sexe: 'tous', // tous | F | M | X (X = mixte, règle documentée dans DATA_MODEL.md)
  lettresMin: null,
  lettresMax: null,
  initiale: '',
  terminaison: '',
  accent: 'tous', // tous | avec | sans
  compose: 'tous', // tous | oui | non
  fiche: 'tous', // tous | enrichies (partielles ou complètes) | completes
  tri: 'popularite', // popularite | alpha
}

/**
 * Filtre la liste des prénoms de l'index selon les critères.
 * La liste d'entrée est déjà triée par popularité cumulée décroissante.
 */
export function filtrer(prenoms, criteres) {
  const c = { ...CRITERES_VIDES, ...criteres }
  const texte = normaliser(c.texte.trim())
  const initiale = normaliser(c.initiale.trim()).slice(0, 1)
  const terminaison = normaliser(c.terminaison.trim())

  const resultats = prenoms.filter((p) =>
    (c.sexe === 'tous' || p.sexe === c.sexe) &&
    (c.lettresMin == null || c.lettresMin === '' || p.lettres >= Number(c.lettresMin)) &&
    (c.lettresMax == null || c.lettresMax === '' || p.lettres <= Number(c.lettresMax)) &&
    (!initiale || p.norm.startsWith(initiale)) &&
    (!terminaison || p.norm.endsWith(terminaison)) &&
    (c.accent === 'tous' || (c.accent === 'avec') === p.accent) &&
    (c.compose === 'tous' || (c.compose === 'oui') === p.compose) &&
    (c.fiche === 'tous' || (c.fiche === 'completes' ? p.qualite === 'c' : p.qualite !== 'm')) &&
    (!texte || p.norm.includes(texte)),
  )

  if (c.tri === 'alpha') {
    resultats.sort((a, b) => a.affichage.localeCompare(b.affichage, 'fr'))
  } else if (texte) {
    // Les prénoms qui commencent par le texte passent devant (ordre de popularité conservé).
    const debut = resultats.filter((p) => p.norm.startsWith(texte))
    const reste = resultats.filter((p) => !p.norm.startsWith(texte))
    return [...debut, ...reste]
  }
  return resultats
}
