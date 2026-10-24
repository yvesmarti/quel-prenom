// Calculs géographiques pour la carte d'un prénom (définitions : STATISTIQUES.md).
//
// Part locale   = effectif du prénom dans la zone / total des effectifs publiés dans la zone
// Indice        = part locale / part sur l'ensemble des zones du même niveau × 100
//                 (100 = aussi fréquent que dans l'ensemble ; 200 = deux fois plus fréquent)
// Les deux parts utilisent le même type de dénominateur (somme des effectifs publiés au même
// niveau géographique), ce qui limite l'effet des prénoms rares non publiés.

/** Décennies disponibles dans les lignes [[code, decennie, valeur], …]. */
export function periodes(anneeMin, anneeMax) {
  const res = []
  for (let d = Math.floor(anneeMin / 10) * 10; d <= anneeMax; d += 10) res.push(d)
  return res
}

/**
 * lignes : [[code, decennie, valeur]] du prénom pour un sexe et un niveau ;
 * totaux : {code: {F: {decennie: total}, M: …}} ; periode : décennie (nombre) ou 'tout'.
 * Renvoie [{code, valeur, total, part, indice}] pour toutes les zones du niveau.
 */
export function valeursParZone(lignes, totaux, sexe, periode, minIndice) {
  const garder = (dec) => periode === 'tout' || Number(dec) === Number(periode)
  const parZone = new Map()
  for (const [code, dec, v] of lignes || []) if (garder(dec)) parZone.set(code, (parZone.get(code) ?? 0) + v)

  const zones = Object.keys(totaux).map((code) => {
    const total = Object.entries(totaux[code][sexe] || {}).reduce((s, [d, t]) => s + (garder(d) ? t : 0), 0)
    return { code, valeur: parZone.get(code) ?? 0, total }
  })
  const sommeValeurs = zones.reduce((s, z) => s + z.valeur, 0)
  const sommeTotaux = zones.reduce((s, z) => s + z.total, 0)
  const partGlobale = sommeTotaux ? sommeValeurs / sommeTotaux : 0
  for (const z of zones) {
    z.part = z.total ? z.valeur / z.total : null
    z.indice = z.valeur >= minIndice && partGlobale ? (z.part / partGlobale) * 100 : null
  }
  return zones
}

/** Zones de prédilection : indice le plus élevé parmi les zones à effectif suffisant. */
export function predilection(zones, nombre = 5) {
  return zones.filter((z) => z.indice != null).sort((a, b) => b.indice - a.indice || a.code.localeCompare(b.code))
    .slice(0, nombre)
}

/** Clé de tri d'un code de département : 01…19, 2A, 2B, 21…95, 971… */
const numeroDepartement = (code) => (/^2[AB]$/.test(code) ? 20 : Number(code))

/** Zones triées pour les listes : régions par nom, départements par code. */
export function zonesTriees(noms, niveau) {
  const entrees = Object.entries(noms || {})
  return niveau === 'REG'
    ? entrees.sort((a, b) => a[1].localeCompare(b[1], 'fr'))
    : entrees.sort((a, b) => numeroDepartement(a[0]) - numeroDepartement(b[0]) || a[0].localeCompare(b[0]))
}
