import { reactive, watch } from 'vue'
import { lire, ecrire, classer, oublier, annuler, selectionVide, nettoyer } from './selection.js'

// Sélection du visiteur, conservée entre les visites (voir selection.js) et partagée entre les pages.
export const selection = reactive(lire())

watch(selection, () => ecrire(JSON.parse(JSON.stringify(selection))), { deep: true })

export const garder = (id) => classer(selection, id, 'garder')
export const ecarter = (id) => classer(selection, id, 'ecarter')
export const revoirPlusTard = (id) => classer(selection, id, 'plusTard')
export const remettre = (id) => oublier(selection, id)
export const annulerDernier = () => annuler(selection)

export function remplacer(nouvelle) {
  Object.assign(selection, nettoyer(nouvelle))
}

export function toutEffacer() {
  Object.assign(selection, selectionVide())
}
