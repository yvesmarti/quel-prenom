<script setup>
import { ref, computed, watch } from 'vue'
import { chargerIndex, chargerMeta, chargerSeries } from '../lib/dataLoader.js'
import { environ } from '../lib/normalize.js'
import CourbeNationale from '../components/CourbeNationale.vue'

const props = defineProps({ id: { type: String, required: true } })

const LIBELLES_USAGE = { F: 'Usage féminin', M: 'Usage masculin', X: 'Usage mixte' }
const NOMS = { F: 'Filles', M: 'Garçons' }

const prenom = ref(null)
const autresGraphies = ref([])
const series = ref(null)
const meta = ref(null)
const mesure = ref('valeur')
const etat = ref('chargement') // chargement | ok | introuvable | erreur

async function charger() {
  etat.value = 'chargement'
  try {
    const [index, m] = await Promise.all([chargerIndex(), chargerMeta()])
    meta.value = m
    const p = index.find((x) => x.id === props.id)
    if (!p) { etat.value = 'introuvable'; return }
    prenom.value = p
    autresGraphies.value = index.filter((x) => x.norm === p.norm && x.id !== p.id)
    series.value = await chargerSeries(p)
    etat.value = 'ok'
    document.title = `${p.affichage} — Prénoscope`
  } catch {
    etat.value = 'erreur'
  }
}
watch(() => props.id, charger, { immediate: true })

// Résumé par sexe, calculé à partir des données publiées (effectifs arrondis, rangs officiels).
const resumes = computed(() => ['F', 'M'].filter((s) => series.value?.[s]).map((sexe) => {
  const points = series.value[sexe]
  const meilleur = points.reduce((a, b) => (b[2] < a[2] ? b : a))
  const maxi = points.reduce((a, b) => (b[1] > a[1] ? b : a))
  const dernier = points[points.length - 1]
  return { sexe, nbAnnees: points.length, meilleur, maxi, dernier }
}))

const partMinoritaire = computed(() => {
  const p = prenom.value
  return p && p.total ? Math.min(p.totalF, p.totalM) / p.total : 0
})
</script>

<template>
  <RouterLink to="/" class="retour">← Retour à la recherche</RouterLink>

  <div v-if="etat === 'chargement'" role="status" class="etat">Chargement de la fiche…</div>
  <div v-else-if="etat === 'introuvable'" role="alert" class="etat">
    Ce prénom ne figure pas dans le fichier de l'Insee (graphie « {{ id }} »).
  </div>
  <div v-else-if="etat === 'erreur'" role="alert" class="etat">
    La fiche n'a pas pu être chargée. <button class="bouton" @click="charger">Réessayer</button>
  </div>

  <article v-else class="fiche">
    <header class="carte entete">
      <h1>{{ prenom.affichage }}</h1>
      <p class="sous-titre">
        <span :class="['badge', prenom.sexe]">{{ LIBELLES_USAGE[prenom.sexe] }}</span>
        <span class="doux">
          {{ prenom.lettres }} lettres<template v-if="prenom.compose"> · composé</template>
          · graphie Insee : {{ prenom.id.toUpperCase() }}
        </span>
      </p>
      <p class="doux petit">
        Environ {{ prenom.total.toLocaleString('fr-FR') }} naissances en France entre
        {{ prenom.premiereAnnee }} et {{ prenom.derniereAnnee }}<template v-if="prenom.totalF && prenom.totalM">
          (filles : {{ environ(prenom.totalF) }}, garçons : {{ environ(prenom.totalM) }},
          soit {{ (partMinoritaire * 100).toLocaleString('fr-FR', { maximumFractionDigits: 1 }) }} %
          pour le sexe le moins représenté ; « mixte » à partir de {{ meta.regles.seuil_mixte * 100 }} %)</template>.
      </p>
    </header>

    <section class="carte" aria-labelledby="titre-courbe">
      <div class="titre-section">
        <h2 id="titre-courbe">Popularité en France depuis {{ meta.annee_min }}</h2>
        <div class="segments" role="group" aria-label="Mesure affichée">
          <button :aria-pressed="mesure === 'valeur'" @click="mesure = 'valeur'">Naissances</button>
          <button :aria-pressed="mesure === 'rang'" @click="mesure = 'rang'">Rang</button>
        </div>
      </div>
      <CourbeNationale :series="series" :mesure="mesure" :annee-min="meta.annee_min" :annee-max="meta.annee_max" />
      <p class="doux petit note">
        <template v-if="mesure === 'valeur'">Effectifs arrondis par l'Insee au multiple de 5 : ce sont des ordres de grandeur.</template>
        <template v-else>Rang officiel Insee parmi les prénoms du même sexe (1 = le plus donné), échelle logarithmique.</template>
        Une année sans point signifie que le prénom n'apparaît pas dans le fichier cette année-là
        (effectif nul ou trop faible après arrondi), pas forcément zéro naissance.
      </p>

      <dl class="resumes">
        <div v-for="r in resumes" :key="r.sexe" class="resume">
          <dt>{{ NOMS[r.sexe] }}</dt>
          <dd>Meilleur rang : <strong>{{ r.meilleur[2] }}<sup>e</sup></strong> en {{ r.meilleur[0] }}</dd>
          <dd>Année la plus forte : {{ r.maxi[0] }} ({{ environ(r.maxi[1]) }})</dd>
          <dd>Dernière année présente : {{ r.dernier[0] }} ({{ environ(r.dernier[1]) }}, rang {{ r.dernier[2] }})</dd>
          <dd class="doux">Présent {{ r.nbAnnees }} année{{ r.nbAnnees > 1 ? 's' : '' }} sur {{ meta.annee_max - meta.annee_min + 1 }}</dd>
        </div>
      </dl>
    </section>

    <section v-if="autresGraphies.length" class="carte" aria-labelledby="titre-graphies">
      <h2 id="titre-graphies">Autres graphies, mêmes lettres sans accents</h2>
      <p class="doux petit">L'Insee les compte séparément ; Prénoscope ne les fusionne pas.</p>
      <ul class="graphies">
        <li v-for="g in autresGraphies" :key="g.id">
          <RouterLink :to="{ name: 'fiche', params: { id: g.id } }">{{ g.affichage }}</RouterLink>
          <span class="doux petit"> {{ environ(g.total) }}</span>
        </li>
      </ul>
    </section>

    <section class="carte doux petit" aria-labelledby="titre-sources">
      <h2 id="titre-sources" class="h-petit">Ce que contient cette fiche</h2>
      <p>
        Fiche <strong>minimale</strong> : statistiques nationales de l'Insee uniquement.
        L'origine, l'étymologie et les personnalités associées ne sont pas encore documentées
        et ne seront ajoutées qu'avec des sources vérifiables.
      </p>
      <p>Source : {{ meta.source.organisme }}, {{ meta.source.titre }} — {{ meta.source.licence }}.</p>
    </section>
  </article>
</template>

<style scoped>
.retour { display: inline-block; margin-bottom: 16px; text-decoration: none; }
.etat { padding: 24px 0; }
.fiche { display: grid; gap: 16px; }
.entete h1 { font-size: 2.6rem; margin: 0 0 8px; color: var(--accent); }
.sous-titre { display: flex; flex-wrap: wrap; gap: 8px 12px; align-items: center; margin: 0 0 8px; }
.titre-section { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 8px; }
h2 { font-size: 1.25rem; margin: 0 0 8px; }
.h-petit { font-size: 1rem; }
.segments { display: flex; gap: 4px; background: var(--surface-douce); padding: 3px; border-radius: 999px; }
.segments button { border: 0; background: transparent; padding: 5px 14px; border-radius: 999px; cursor: pointer; }
.segments button[aria-pressed='true'] { background: var(--surface); color: var(--accent); font-weight: 600; box-shadow: var(--ombre); }
.note { margin: 4px 0 12px; }
.resumes { display: grid; gap: 12px; margin: 0; }
@media (min-width: 640px) { .resumes { grid-template-columns: 1fr 1fr; } }
.resume { background: var(--fond); border-radius: 10px; padding: 12px 14px; }
.resume dt { font-weight: 700; margin-bottom: 4px; }
.resume dd { margin: 0; }
.graphies { list-style: none; padding: 0; margin: 0; display: flex; flex-wrap: wrap; gap: 8px 18px; }
.graphies a { font-family: var(--serif); font-size: 1.1rem; }
</style>
