// Libellés et définitions des tendances (calculées par pipeline/stats.py, voir STATISTIQUES.md).
// Les seuils viennent de meta.regles.tendances : le texte reste juste si on les modifie.

export const ORDRE_TENDANCES = ['emergent', 'progression', 'retour', 'vagues', 'declin', 'devenu_rare']

export const LIBELLES_TENDANCES = {
  emergent: 'Émergent',
  progression: 'Forte progression',
  retour: 'Retour',
  vagues: 'Plusieurs vagues',
  declin: 'En déclin',
  devenu_rare: 'Devenu rare',
}

/** Définition en une phrase, avec les seuils réels. Y = dernière année du millésime. */
export function definitionTendance(cat, t, Y) {
  const L = t.fenetre
  const recent = `${Y - L + 1}–${Y}`
  const ancien = `${Y - t.decalage_progression - L + 1}–${Y - t.decalage_progression}`
  return {
    emergent: `Apparu dans le fichier national en ${Y - t.emergent_depuis + 1} ou après, et donné au moins ${t.emergent_min} fois par an en moyenne sur ${recent}.`,
    progression: `Fréquence (pour 1 000 naissances) au moins multipliée par ${t.progression_facteur} entre ${ancien} et ${recent}, avec au moins ${t.progression_min} naissances par an sur ${recent} et ${t.progression_min_avant} sur ${ancien}.`,
    declin: `Fréquence au moins divisée par ${1 / t.declin_facteur} entre ${ancien} et ${recent}, pour un prénom donné au moins ${t.declin_min_avant} fois par an sur ${ancien}.`,
    devenu_rare: `A dépassé ${t.rare_pic_min} naissances par an (moyenne sur 5 ans) à son apogée, mais pas plus de ${t.rare_recent_max} par an sur ${recent}.`,
    vagues: `Au moins deux sommets de popularité (rang officiel lissé sur ${t.lissage_rang} ans, meilleur que ${t.vague_rang_max}) séparés par un creux où le rang est au moins ${Math.round(10 ** t.vague_prominence)} fois moins bon.`,
    retour: `Deux vagues de popularité : un sommet avant ${t.retour_avant} et un autre depuis ${Y - t.retour_recent + 1}, tous deux dans les ${t.retour_rang_max} premiers (rang lissé), séparés par un creux où le rang est au moins ${Math.round(10 ** t.vague_prominence)} fois moins bon.`,
  }[cat]
}
