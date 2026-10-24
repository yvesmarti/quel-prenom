// Indicateurs descriptifs d'une série nationale (un prénom, un sexe).
// Traduction fidèle de la fonction `indicateurs` de pipeline/stats.py (hors tendances) :
// les tests comparent les deux calculs sur un échantillon exporté par le pipeline.

const arrondi = (x, d) => Math.round(x * 10 ** d) / 10 ** d

/** Moyenne annuelle sur [debut..fin] ; une année absente compte pour 0. */
export function moyenne(serie, debut, fin) {
  let s = 0
  for (let a = debut; a <= fin; a++) s += serie.get(a) ?? 0
  return s / (fin - debut + 1)
}

/**
 * points : [[annee, valeur, rang], …] ; naissances : {annee: {F, M}} (années ≥ 1946) ;
 * nbPublies : {annee: {F, M}} ; regles : meta.regles ; anneeMax : dernière année du millésime.
 */
export function indicateurs(points, sexe, naissances, nbPublies, regles, anneeMax) {
  const Y = anneeMax
  const valeur = new Map(points.map((p) => [p[0], p[1]]))
  const rang = new Map(points.map((p) => [p[0], p[2]]))
  const freq = new Map()
  for (const [a, n] of Object.entries(naissances)) freq.set(Number(a), (valeur.get(Number(a)) ?? 0) / n[sexe] * 1000)

  const record = points.reduce((m, p) => (p[1] > m[1] || (p[1] === m[1] && p[0] < m[0]) ? p : m))
  const meilleur = points.reduce((m, p) => (p[2] < m[2] || (p[2] === m[2] && p[0] < m[0]) ? p : m))
  const anneesFreq = [...freq.keys()].filter((a) => valeur.has(a))
  const recordFreq = anneesFreq.length
    ? anneesFreq.reduce((m, a) => (freq.get(a) > freq.get(m) || (freq.get(a) === freq.get(m) && a < m) ? a : m))
    : null

  const ind = {
    total: points.reduce((s, p) => s + p[1], 0),
    nb_annees: points.length,
    premiere_annee: points[0][0],
    derniere_annee: points[points.length - 1][0],
    record_effectif: [record[0], record[1]],
    meilleur_rang: [meilleur[0], meilleur[2]],
    record_frequence: recordFreq != null ? [recordFreq, arrondi(freq.get(recordFreq), 3)] : null,
    derniere: valeur.has(Y)
      ? { annee: Y, valeur: valeur.get(Y), rang: rang.get(Y), nb_publies: nbPublies[Y][sexe],
          frequence: freq.has(Y) ? arrondi(freq.get(Y), 3) : null }
      : null,
    evolutions: {},
  }

  for (const k of regles.evolutions) {
    const avant = [Y - k - 2, Y - k]
    const apres = [Y - 2, Y]
    if (avant[0] < regles.annee_debut_frequences) continue
    const eAvant = moyenne(valeur, ...avant)
    const eApres = moyenne(valeur, ...apres)
    const evo = { avant, apres, effectif_avant: arrondi(eAvant, 1), effectif_apres: arrondi(eApres, 1) }
    if (eAvant >= regles.evolution_min && eApres >= regles.evolution_min) {
      evo.variation = arrondi(moyenne(freq, ...apres) / moyenne(freq, ...avant) - 1, 3)
    }
    ind.evolutions[String(k)] = evo
  }
  return ind
}

/** Fréquence pour 1 000 naissances du même sexe, ou null si l'année n'a pas de dénominateur publié. */
export function frequence(valeur, annee, sexe, naissances) {
  const n = naissances[annee]
  return n ? (valeur / n[sexe]) * 1000 : null
}
