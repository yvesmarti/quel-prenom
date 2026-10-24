<script setup>
import { ref, computed, watch } from 'vue'
import { chargerSeries, cleLot } from '../lib/dataLoader.js'
import { normaliser } from '../lib/normalize.js'
import { recentes, classePopularite, stylesDe } from '../lib/suggestions.js'
import { LIBELLES_TENDANCES } from '../lib/tendances.js'

// Une proposition : le prénom, ce qu'on en sait et pourquoi il est proposé. Les chiffres sont ceux de l'Insee.
const props = defineProps({
  prenom: { type: Object, required: true },
  raisons: { type: Array, default: () => [] },
  sexe: { type: String, default: 'tous' }, // sexe visé par le visiteur (tous | F | M | X)
  annee: { type: Number, default: 2025 },
})

const LIBELLES_SEXE = { F: 'Féminin', M: 'Masculin', X: 'Mixte' }
const CODES = { e: 'emergent', p: 'progression', r: 'retour', v: 'vagues', d: 'declin', x: 'devenu_rare' }
const LIBELLES_STYLE = { intemporel: 'Intemporel', vintage: 'Vintage', moderne: 'Moderne' }

// Sexe de référence des chiffres : celui demandé, sinon le plus fréquent pour ce prénom.
const sexeChiffres = computed(() => {
  const p = props.prenom
  if (props.sexe === 'F' || props.sexe === 'M') return props.sexe
  return p.recF >= p.recM ? 'F' : 'M'
})
const effectif = computed(() => {
  const n = recentes(props.prenom, sexeChiffres.value)
  return n < 10 ? 'moins de 10' : `environ ${(Math.round(n / 5) * 5).toLocaleString('fr-FR')}`
})
const rang = computed(() => (sexeChiffres.value === 'F' ? props.prenom.rangF : props.prenom.rangM))
const qui = computed(() => (sexeChiffres.value === 'F' ? 'filles' : 'garçons'))
const tendances = computed(() => [...props.prenom.tend].map((c) => LIBELLES_TENDANCES[CODES[c]]).filter(Boolean))
const styles = computed(() => stylesDe(props.prenom).map((s) => LIBELLES_STYLE[s]))
const popularite = computed(() => ({ courant: 'Très courant', connu: 'Connu', rare: 'Rare' }[classePopularite(props.prenom, sexeChiffres.value)]))

// --- Courbe nationale (chargée à la demande, sans bibliothèque de graphiques) ---
const serie = ref(null)
watch(() => props.prenom.id, async (id) => {
  serie.value = null
  try {
    const s = await chargerSeries({ id, lot: cleLot(normaliser(id)) })
    if (id === props.prenom.id) serie.value = s[sexeChiffres.value] || null
  } catch { /* la carte reste utilisable sans courbe */ }
}, { immediate: true })

const L = 240
const H = 56
const trace = computed(() => {
  const pts = serie.value
  if (!pts?.length) return ''
  const max = Math.max(...pts.map((x) => x[1]), 1)
  const x = (a) => ((a - 1900) / (props.annee - 1900)) * L
  const y = (v) => H - 3 - (v / max) * (H - 8)
  let d = ''
  let precedent = null
  for (const [a, v] of pts) {
    d += `${precedent === a - 1 ? 'L' : 'M'}${x(a).toFixed(1)} ${y(v).toFixed(1)}`
    precedent = a
  }
  return d
})
const resume = computed(() => {
  const pts = serie.value
  if (!pts?.length) return ''
  const pic = pts.reduce((m, x) => (x[1] > m[1] ? x : m))
  return `Courbe des naissances par an depuis 1900. Record en ${pic[0]}.`
})
</script>

<template>
  <article class="carte-prenom" aria-live="polite">
    <header>
      <h2>{{ prenom.affichage }}</h2>
      <span :class="['badge', prenom.sexe]">{{ LIBELLES_SEXE[prenom.sexe] }}</span>
    </header>

    <p v-if="raisons.length" class="raisons">
      <span v-for="r in raisons" :key="r" class="etiquette">{{ r }}</span>
    </p>

    <p class="chiffres">
      <strong>{{ effectif }}</strong> naissances par an ces dernières années
      <template v-if="sexe === 'tous' && prenom.sexe === 'X'">({{ qui }}, le sexe le plus fréquent)</template>
      <template v-else-if="prenom.sexe === 'X'">({{ qui }})</template>
      <template v-if="rang"> · {{ rang.toLocaleString('fr-FR') }}<sup>e</sup> au classement des {{ qui }} en {{ annee }}</template>
    </p>

    <figure v-if="trace" class="courbe">
      <svg :viewBox="`0 0 ${L} ${H}`" role="img" :aria-label="resume" preserveAspectRatio="none">
        <path :d="trace" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round" />
      </svg>
      <figcaption class="doux petit"><span>1900</span><span>{{ annee }}</span></figcaption>
    </figure>

    <p class="meta doux petit">
      {{ popularite }} · {{ prenom.lettres }} lettres, environ {{ prenom.syllabes }} syllabe{{ prenom.syllabes > 1 ? 's' : '' }}
      <template v-if="styles.length"> · {{ styles.join(', ') }}</template>
      <template v-if="tendances.length"> · {{ tendances.join(', ') }}</template>
    </p>
    <p v-if="prenom.origines.length" class="meta doux petit">Origine : {{ prenom.origines.join(', ') }}</p>

    <RouterLink :to="{ name: 'fiche', params: { id: prenom.id } }" class="fiche">Voir la fiche complète</RouterLink>
  </article>
</template>

<style scoped>
.carte-prenom { display: grid; gap: 10px; }
header { display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap; }
h2 { font-size: 2.6rem; margin: 0; line-height: 1.1; word-break: break-word; }
.raisons { display: flex; flex-wrap: wrap; gap: 6px; margin: 0; }
.etiquette { font-size: 0.8rem; padding: 2px 10px; border-radius: 999px; background: var(--accent-fond); color: var(--accent); }
.chiffres, .meta { margin: 0; }
.courbe { margin: 4px 0 0; color: var(--accent); }
.courbe svg { width: 100%; height: 56px; display: block; background: var(--surface-douce); border-radius: 8px; }
figcaption { display: flex; justify-content: space-between; }
.fiche { justify-self: start; }
</style>
