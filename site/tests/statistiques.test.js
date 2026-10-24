// Statistiques du site comparées aux calculs Python du pipeline, sur les données publiées.
import { readFileSync, existsSync } from 'node:fs'
import { describe, it, expect } from 'vitest'
import { indicateurs, moyenne } from '../src/lib/indicateurs.js'
import { valeursParZone, predilection, zonesTriees } from '../src/lib/geo.js'
import { avecRangOfficiel, avecRangCalcule } from '../src/lib/classements.js'
import { cleLot, decoderIndex } from '../src/lib/dataLoader.js'

const lire = (chemin) => JSON.parse(readFileSync(new URL(chemin, import.meta.url), 'utf-8'))
const meta = lire('../public/data/meta.json')
const echantillon = lire('./fixtures/indicateurs_python.json')
const index = decoderIndex(lire('../public/data/index.v1.json'))

function series(id) {
  const p = index.find((x) => x.id === id)
  return lire(`../public/data/prenoms/${p.lot}.json`).prenoms[id]
}

/** Compare deux valeurs JSON en tolérant les écarts d'arrondi (≤ 0,001). */
function proche(a, b) {
  if (typeof a === 'number' && typeof b === 'number') return Math.abs(a - b) <= 1e-3 + 1e-9
  if (Array.isArray(a) && Array.isArray(b)) return a.length === b.length && a.every((x, i) => proche(x, b[i]))
  if (a && b && typeof a === 'object' && typeof b === 'object') {
    const cles = new Set([...Object.keys(a), ...Object.keys(b)])
    return [...cles].every((k) => proche(a[k], b[k]))
  }
  return a === b
}

describe('indicateurs', () => {
  it(`identiques au pipeline Python sur ${echantillon.length} séries`, () => {
    const differences = []
    for (const { id, sexe, indicateurs: attendu } of echantillon) {
      const calcule = indicateurs(series(id)[sexe], sexe, meta.naissances, meta.nb_publies, meta.regles, meta.annee_max)
      if (!proche(calcule, attendu)) differences.push({ id, sexe, calcule, attendu })
    }
    expect(differences).toEqual([])
  })
  it('moyenne : année absente = 0', () => {
    expect(moyenne(new Map([[2020, 10]]), 2020, 2021)).toBe(5)
  })
})

describe('géographie', () => {
  const totaux = lire('../public/data/geo/totaux.json').totaux
  const geoLea = lire(`../public/data/geo/prenoms/g_${cleLot('lea', 3)}.json`).prenoms['léa']

  it('indice 100 en moyenne pondérée et zones à faible effectif exclues', () => {
    const zones = valeursParZone(geoLea.F.REG, totaux.REG, 'F', 'tout', meta.regles.geo_min_indice)
    expect(zones.length).toBe(Object.keys(totaux.REG).length)
    const somme = zones.reduce((s, z) => s + z.valeur, 0)
    const total = zones.reduce((s, z) => s + z.total, 0)
    const moyennePonderee = zones.reduce((s, z) => s + (z.indice ?? 0) * z.total, 0) / total
    if (zones.every((z) => z.indice != null)) expect(moyennePonderee).toBeCloseTo(100, 6)
    expect(somme).toBe(geoLea.F.REG.reduce((s, l) => s + l[2], 0))
    for (const z of zones) if (z.valeur < meta.regles.geo_min_indice) expect(z.indice).toBeNull()
  })
  it('zones de prédilection triées par indice', () => {
    const zones = valeursParZone(geoLea.F.DEP, totaux.DEP, 'F', 2000, meta.regles.geo_min_indice)
    const top = predilection(zones, 5)
    expect(top.length).toBe(5)
    for (let i = 1; i < top.length; i++) expect(top[i - 1].indice).toBeGreaterThanOrEqual(top[i].indice)
  })
  it('chaque lot géographique attendu existe', () => {
    const manquants = index.slice(0, 3000).map((p) => cleLot(p.norm, 3))
      .filter((c, i, t) => t.indexOf(c) === i)
      .filter((c) => !existsSync(new URL(`../public/data/geo/prenoms/g_${c}.json`, import.meta.url)))
    // Un lot peut manquer seulement si aucun de ses prénoms n'a de données régionales.
    for (const c of manquants) {
      expect(index.filter((p) => cleLot(p.norm, 3) === c && p.total > 1000)).toEqual([])
    }
  })
})

describe('classements', () => {
  it('rang officiel = position', () => {
    const c = lire('../public/data/classements/france/2025.json')
    const liste = avecRangOfficiel(c.F.top)
    expect(liste[0].rang).toBe(1)
    expect(liste.at(-1).rang).toBe(c.F.top.length)
  })
  it('rang calculé : les ex æquo partagent le même rang', () => {
    expect(avecRangCalcule([['a', 10], ['b', 8], ['c', 8], ['d', 5]]).map((x) => x.rang)).toEqual([1, 2, 2, 4])
  })
})

describe('clés de lot et zones', () => {
  it('cleLot(norm, 2) redonne la clé calculée par le pipeline pour tous les prénoms', () => {
    expect(index.filter((p) => cleLot(p.norm, 2) !== p.lot)).toEqual([])
  })
  it('départements triés par code, 2A et 2B entre 19 et 21', () => {
    const codes = zonesTriees(lire('../public/data/geo/zones.json').DEP, 'DEP').map(([c]) => c)
    const i = codes.indexOf('19')
    expect(codes.slice(i, i + 4)).toEqual(['19', '2A', '2B', '21'])
    expect(codes.at(-1)).toBe('976')
  })
})
