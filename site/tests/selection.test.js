import { describe, it, expect } from 'vitest'
import {
  selectionVide, nettoyer, lire, ecrire, classer, annuler, oublier, encoderPartage, decoderPartage,
  exporterJson, importerJson, CLE_STOCKAGE,
} from '../src/lib/selection.js'

const faux = () => {
  const m = new Map()
  return { getItem: (k) => m.get(k) ?? null, setItem: (k, v) => m.set(k, v) }
}

describe('stockage', () => {
  it('relit ce qui a été écrit', () => {
    const s = faux()
    const sel = selectionVide()
    classer(sel, 'léa', 'garder')
    expect(ecrire(sel, s)).toBe(true)
    expect(lire(s).gardes).toEqual(['léa'])
  })
  it('fonctionne sans stockage (bloqué, absent, corrompu)', () => {
    const bloque = { getItem() { throw new Error('bloqué') }, setItem() { throw new Error('bloqué') } }
    expect(lire(bloque)).toEqual(selectionVide())
    expect(ecrire(selectionVide(), bloque)).toBe(false)
    const corrompu = faux()
    corrompu.setItem(CLE_STOCKAGE, '{pas du json')
    expect(lire(corrompu)).toEqual(selectionVide())
    expect(lire(undefined)).toEqual(selectionVide())
  })
  it('ignore les données mal formées', () => {
    const sel = nettoyer({ gardes: ['a', 3, null], prefs: { sexe: 'F', origines: 'latin', style: 12 }, questionnaire: 'x' })
    expect(sel.gardes).toEqual(['a'])
    expect(sel.prefs.sexe).toBe('F')
    expect(sel.prefs.origines).toEqual([])
    expect(sel.prefs.style).toBe('tous')
    expect(sel.questionnaire).toBe('a_faire')
  })
})

describe('gestes', () => {
  it('un prénom n’est que dans une liste à la fois', () => {
    const sel = selectionVide()
    classer(sel, 'jade', 'garder')
    classer(sel, 'jade', 'ecarter')
    expect(sel.gardes).toEqual([])
    expect(sel.ecartes).toEqual(['jade'])
  })
  it('annule le dernier geste', () => {
    const sel = selectionVide()
    classer(sel, 'emma', 'garder')
    classer(sel, 'lou', 'plusTard')
    expect(annuler(sel)).toBe('lou')
    expect(sel.plusTard).toEqual([])
    expect(sel.gardes).toEqual(['emma'])
    expect(annuler(selectionVide())).toBeNull()
  })
  it('remet un prénom en circulation', () => {
    const sel = selectionVide()
    classer(sel, 'emma', 'ecarter')
    oublier(sel, 'emma')
    expect(sel.ecartes).toEqual([])
  })
})

describe('partage', () => {
  it('fait l’aller-retour, y compris avec accents, tirets et apostrophes', () => {
    const ids = ['léa', 'marie-claire', "m'hamed", 'zoé']
    expect(decoderPartage(encoderPartage(ids))).toEqual(ids)
  })
  it('se protège des entrées absurdes', () => {
    expect(decoderPartage('')).toEqual([])
    expect(decoderPartage('%E0%A4%A,léa,léa,' + 'x'.repeat(100))).toEqual(['léa'])
    expect(decoderPartage(Array.from({ length: 500 }, (_, i) => `n${i}`).join(',')).length).toBe(200)
  })
  it('exporte et réimporte un fichier', () => {
    const sel = selectionVide()
    classer(sel, 'léa', 'garder')
    expect(importerJson(exporterJson(sel)).gardes).toEqual(['léa'])
    expect(importerJson('pas du json')).toBeNull()
    expect(importerJson('{"a":1}')).toBeNull()
  })
})
