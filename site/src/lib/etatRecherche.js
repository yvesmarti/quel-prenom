import { reactive } from 'vue'
import { CRITERES_VIDES } from './filters.js'

// Critères conservés pendant la visite : en revenant d'une fiche, la recherche est intacte.
export const etatRecherche = {
  criteres: reactive({ ...CRITERES_VIDES }),
  affiches: 60,
}
