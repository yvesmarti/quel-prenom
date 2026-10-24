// Mise en forme des données encyclopédiques (aucune donnée n'est ajoutée ici).

export const ORDRE_VARIANTES = ['orthographique', 'equivalent_autre_genre', 'diminutif', 'compose',
  'apparente', 'reputee_identique', 'traduction']

export const LIBELLES_VARIANTES = {
  orthographique: 'Variantes orthographiques',
  equivalent_autre_genre: "Équivalent dans l'autre genre",
  diminutif: 'Diminutifs',
  compose: 'Prénoms composés',
  apparente: 'Prénoms apparentés',
  reputee_identique: 'Formes réputées identiques (autres langues, Wikidata)',
  traduction: 'Équivalents dans d’autres langues',
}

/**
 * Regroupe les variantes du Wiktionnaire et de Wikidata par type, sans doublon de libellé
 * (comparaison sensible aux accents, insensible à la casse), en excluant le prénom lui-même.
 */
export function regrouperVariantes(wiktionnaire, wikidata, idPrenom) {
  const groupes = new Map()
  for (const v of [...wiktionnaire, ...wikidata]) {
    if (!v.libelle || v.libelle.toLowerCase() === idPrenom) continue
    if (!groupes.has(v.type)) groupes.set(v.type, new Map())
    const cle = v.libelle.toLowerCase() + '|' + (v.langue ?? '')
    if (!groupes.get(v.type).has(cle)) groupes.get(v.type).set(cle, v)
  }
  return ORDRE_VARIANTES.filter((t) => groupes.has(t)).map((type) => ({
    type,
    items: [...groupes.get(type).values()].sort((a, b) => (a.langue ?? '').localeCompare(b.langue ?? '', 'fr')
      || a.libelle.localeCompare(b.libelle, 'fr')),
  }))
}
