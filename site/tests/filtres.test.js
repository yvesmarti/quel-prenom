// Tests sur l'index réellement publié (public/data/index.v1.json).
import { readFileSync } from 'node:fs'
import { describe, it, expect } from 'vitest'
import { normaliser } from '../src/lib/normalize.js'
import { filtrer } from '../src/lib/filters.js'
import { decoderIndex } from '../src/lib/dataLoader.js'

const index = decoderIndex(JSON.parse(readFileSync(new URL('../public/data/index.v1.json', import.meta.url), 'utf-8')))

describe('normalisation', () => {
  it('donne le même résultat que le pipeline Python pour tous les prénoms', () => {
    const differences = index.filter((p) => normaliser(p.id) !== p.norm)
    expect(differences).toEqual([])
  })
  it('retire accents et ligatures', () => {
    expect(normaliser('Chlöé')).toBe('chloe')
    expect(normaliser('Ælis')).toBe('aelis')
  })
})

describe('filtres', () => {
  it('sans critère, renvoie tout l’index', () => {
    expect(filtrer(index, {}).length).toBe(index.length)
  })
  it('la recherche ignore les accents mais garde les graphies distinctes', () => {
    const ids = filtrer(index, { texte: 'LÉA' }).map((p) => p.id)
    expect(ids).toContain('léa')
    expect(ids).toContain('lea')
    expect(filtrer(index, { texte: 'lea' })[0].norm.startsWith('lea')).toBe(true)
  })
  it('combine sexe, lettres, initiale, terminaison, accent et composé', () => {
    const r = filtrer(index, {
      sexe: 'F', lettresMin: 5, lettresMax: 7, initiale: 'é', terminaison: 'INE', accent: 'avec', compose: 'non',
    })
    expect(r.length).toBeGreaterThan(0)
    for (const p of r) {
      expect(p.sexe).toBe('F')
      expect(p.lettres).toBeGreaterThanOrEqual(5)
      expect(p.lettres).toBeLessThanOrEqual(7)
      expect(p.norm.startsWith('e')).toBe(true)
      expect(p.norm.endsWith('ine')).toBe(true)
      expect(p.accent).toBe(true)
      expect(p.compose).toBe(false)
    }
  })
  it('filtre les prénoms mixtes', () => {
    const r = filtrer(index, { sexe: 'X' })
    expect(r.length).toBeGreaterThan(0)
    expect(r.every((p) => p.totalF > 0 && p.totalM > 0)).toBe(true)
  })
  it('les composés contiennent un tiret', () => {
    expect(filtrer(index, { compose: 'oui' }).every((p) => p.id.includes('-'))).toBe(true)
  })
  it('tri alphabétique', () => {
    const r = filtrer(index, { initiale: 'z', tri: 'alpha' }).map((p) => p.affichage)
    expect(r).toEqual([...r].sort((a, b) => a.localeCompare(b, 'fr')))
  })
  it('aucun résultat pour une combinaison impossible', () => {
    expect(filtrer(index, { lettresMin: 30 })).toEqual([])
  })
})
