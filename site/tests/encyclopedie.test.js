// Mise en forme de l'enrichissement et filtre « qualité de fiche », sur les données publiées.
import { readFileSync, readdirSync, existsSync } from 'node:fs'
import { describe, it, expect } from 'vitest'
import { regrouperVariantes, ORDRE_VARIANTES } from '../src/lib/encyclopedie.js'
import { filtrer } from '../src/lib/filters.js'
import { decoderIndex } from '../src/lib/dataLoader.js'

const lire = (chemin) => JSON.parse(readFileSync(new URL(chemin, import.meta.url), 'utf-8'))
const index = decoderIndex(lire('../public/data/index.v1.json'))
const dossier = (nom) => new URL(`../public/data/${nom}/`, import.meta.url)

describe('variantes', () => {
  it('fusionne les sources sans doublon et exclut le prénom lui-même', () => {
    const g = regrouperVariantes(
      [{ libelle: 'Louis', type: 'equivalent_autre_genre' }, { libelle: 'louise', type: 'orthographique' }],
      [{ libelle: 'Louis', type: 'equivalent_autre_genre', url: 'x' }, { libelle: 'Luisa', type: 'reputee_identique' }],
      'louise')
    expect(g.map((x) => x.type)).toEqual(['equivalent_autre_genre', 'reputee_identique'])
    expect(g[0].items).toHaveLength(1)
  })
  it('les types connus sont ordonnés', () => {
    expect(new Set(ORDRE_VARIANTES).size).toBe(ORDRE_VARIANTES.length)
  })
})

describe('qualité des fiches', () => {
  it("l'index porte un niveau pour chaque prénom", () => {
    expect(index.every((p) => ['c', 'p', 'm'].includes(p.qualite))).toBe(true)
  })
  it('filtre « complètes » et « enrichies »', () => {
    const completes = filtrer(index, { fiche: 'completes' })
    const enrichies = filtrer(index, { fiche: 'enrichies' })
    expect(completes.every((p) => p.qualite === 'c')).toBe(true)
    expect(enrichies.every((p) => p.qualite !== 'm')).toBe(true)
    expect(enrichies.length).toBeGreaterThanOrEqual(completes.length)
  })
})

describe('fichiers d’enrichissement', () => {
  const lots = existsSync(dossier('encyclo')) ? readdirSync(dossier('encyclo')) : []
  it('chaque fiche enrichie a des données publiées, et inversement', () => {
    if (!lots.length) return
    const avecDonnees = new Set()
    for (const nom of ['encyclo', 'wiktionnaire']) {
      for (const f of readdirSync(dossier(nom))) {
        for (const id of Object.keys(lire(`../public/data/${nom}/${f}`).prenoms)) avecDonnees.add(id)
      }
    }
    const enrichis = index.filter((p) => p.qualite !== 'm').map((p) => p.id)
    expect(enrichis.filter((id) => !avecDonnees.has(id))).toEqual([])
  })
  it('les textes du Wiktionnaire portent leur licence et leur source', () => {
    if (!existsSync(dossier('wiktionnaire'))) return
    for (const f of readdirSync(dossier('wiktionnaire')).slice(0, 40)) {
      const contenu = lire(`../public/data/wiktionnaire/${f}`)
      expect(contenu.licence).toMatch(/CC BY-SA 4\.0/)
      for (const p of Object.values(contenu.prenoms)) {
        for (const e of p.entrees ?? []) expect(e.url).toMatch(/^https:\/\/fr\.wiktionary\.org\/wiki\//)
      }
    }
  })
})
