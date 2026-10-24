// Tests du moteur de suggestions sur les profils réellement publiés (public/data/profils.v1.json).
import { readFileSync } from 'node:fs'
import { describe, it, expect } from 'vitest'
import {
  decoderProfils, preferencesVides, suggerer, candidats, apprendre, hasard, classePopularite, classeLongueur,
  stylesDe, convientAuSexe,
} from '../src/lib/suggestions.js'

const profils = decoderProfils(JSON.parse(readFileSync(new URL('../public/data/profils.v1.json', import.meta.url), 'utf-8')))
const parId = new Map(profils.map((p) => [p.id, p]))
const etatVide = () => ({ gardes: [], ecartes: [], vus: [], recents: [] })
const prefs = (surcharge = {}) => ({ ...preferencesVides(), ...surcharge })

describe('profils', () => {
  it('sont assez nombreux et variés', () => {
    expect(profils.length).toBeGreaterThan(5000)
    for (const c of ['courant', 'connu', 'rare']) expect(profils.some((p) => classePopularite(p) === c)).toBe(true)
    for (const s of ['intemporel', 'vintage', 'moderne']) expect(profils.filter((p) => stylesDe(p).includes(s)).length).toBeGreaterThan(100)
  })
  it('classe des exemples connus', () => {
    expect(stylesDe(parId.get('marie'))).toContain('intemporel')
    expect(classeLongueur(parId.get('léa'))).toBe('court')
    expect(classePopularite(parId.get('léa'), 'F')).not.toBe('rare')
  })
})

describe('exclusions strictes', () => {
  it('respectent le sexe, la longueur, les initiales, les composés et les exclus', () => {
    const p = prefs({ sexe: 'F', longueur: 'court', initialesEvitees: ['a', 'm'], compose: 'non', exclus: ['léa'] })
    const { suggestions } = suggerer(profils, p, etatVide(), 50, hasard(1))
    expect(suggestions.length).toBe(50)
    for (const { prenom } of suggestions) {
      expect(convientAuSexe(prenom, 'F')).toBe(true)
      expect(classeLongueur(prenom)).toBe('court')
      expect(['a', 'm']).not.toContain(prenom.initiale)
      expect(prenom.compose).toBe(false)
      expect(prenom.id).not.toBe('léa')
    }
  })
  it('ne propose jamais deux fois le même prénom ni un prénom déjà choisi', () => {
    const etat = { gardes: ['emma', 'jade'], ecartes: ['louise'], vus: ['alice'], recents: [] }
    const { suggestions } = suggerer(profils, prefs({ sexe: 'F' }), etat, 200, hasard(2))
    const ids = suggestions.map((s) => s.prenom.id)
    expect(new Set(ids).size).toBe(ids.length)
    for (const id of ['emma', 'jade', 'louise', 'alice']) expect(ids).not.toContain(id)
  })
})

describe('jamais de liste vide', () => {
  it('assouplit longueur et initiales avant de renoncer, et le dit', () => {
    const p = prefs({ sexe: 'M', longueur: 'long', initialesVoulues: ['w'], origines: ['celtique'] })
    expect(candidats(profils, p).liste.length).toBeGreaterThanOrEqual(30)
    const { suggestions, assouplis } = suggerer(profils, p, etatVide(), 10, hasard(3))
    expect(suggestions.length).toBe(10)
    expect(assouplis.length).toBeGreaterThan(0)
  })
  it('ne signale pas ce qui n’avait pas été demandé', () => {
    expect(suggerer(profils, prefs({ sexe: 'F' }), etatVide(), 5, hasard(4)).assouplis).toEqual([])
  })
})

describe('préférences pondérées', () => {
  it('une popularité « rare » oriente vers des prénoms rares', () => {
    const { suggestions } = suggerer(profils, prefs({ sexe: 'F', popularite: 'rare' }), etatVide(), 20, hasard(5))
    const rares = suggestions.filter((s) => classePopularite(s.prenom, 'F') === 'rare').length
    expect(rares).toBeGreaterThanOrEqual(16)
  })
  it('l’origine souhaitée est favorisée sans pénaliser les prénoms d’origine inconnue', () => {
    const { suggestions } = suggerer(profils, prefs({ origines: ['celtique'] }), etatVide(), 20, hasard(6))
    expect(suggestions.filter((s) => s.prenom.origines.includes('celtique')).length).toBeGreaterThanOrEqual(10)
  })
})

describe('apprentissage', () => {
  it('propose davantage de prénoms proches de ceux qui sont gardés', () => {
    const gardes = ['léa', 'mia', 'eva', 'ava', 'zoé', 'lola', 'nina', 'inès'].filter((id) => parId.has(id))
    const etat = { gardes, ecartes: [], vus: [], recents: [] }
    const { suggestions } = suggerer(profils, prefs({ sexe: 'F' }), etat, 30, hasard(7))
    const moyenne = (l) => l.reduce((s, p) => s + p.lettres, 0) / l.length
    const temoin = suggerer(profils, prefs({ sexe: 'F' }), etatVide(), 30, hasard(7)).suggestions
    expect(moyenne(suggestions.map((s) => s.prenom))).toBeLessThan(moyenne(temoin.map((s) => s.prenom)))
  })
  it('les poids sont positifs pour les prénoms gardés et négatifs pour les écartés', () => {
    const poids = apprendre(parId, ['léa'], ['jean-marie'])
    expect(poids.get('lettres:3')).toBeGreaterThan(0)
    expect(poids.get('compose')).toBeLessThan(0)
  })
})

describe('sans aucune préférence', () => {
  it('le tirage est varié (popularité, longueur, initiales) et reproductible', () => {
    const a = suggerer(profils, prefs({ sexe: 'F' }), etatVide(), 12, hasard(8)).suggestions
    const b = suggerer(profils, prefs({ sexe: 'F' }), etatVide(), 12, hasard(8)).suggestions
    expect(a.map((s) => s.prenom.id)).toEqual(b.map((s) => s.prenom.id))
    expect(new Set(a.map((s) => classePopularite(s.prenom, 'F'))).size).toBeGreaterThanOrEqual(2)
    expect(new Set(a.map((s) => classeLongueur(s.prenom))).size).toBeGreaterThanOrEqual(2)
    expect(new Set(a.map((s) => s.prenom.initiale)).size).toBeGreaterThanOrEqual(7)
  })
})
