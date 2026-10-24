<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { chargerIndex, chargerMeta, chargerSeries } from '../lib/dataLoader.js'
import { environ, normaliser, ordinal, pourcentage } from '../lib/normalize.js'
import { indicateurs } from '../lib/indicateurs.js'
import { LIBELLES_TENDANCES, definitionTendance, ORDRE_TENDANCES } from '../lib/tendances.js'
import CourbeNationale from '../components/CourbeNationale.vue'
import GeographiePrenom from '../components/GeographiePrenom.vue'
import EncyclopediePrenom from '../components/EncyclopediePrenom.vue'

const router = useRouter()
// Retour à la page d'où l'on vient (suggestions, liste, recherche…), sinon à l'accueil.
const retour = () => (window.history.state?.back ? router.back() : router.push('/'))

const props = defineProps({ id: { type: String, required: true } })

const LIBELLES_USAGE = { F: 'Usage féminin', M: 'Usage masculin', X: 'Usage mixte' }
const LIBELLES_QUALITE = { c: 'Fiche complète', p: 'Fiche partielle', m: 'Fiche minimale' }
const NOMS = { F: 'Filles', M: 'Garçons' }
// Couleurs distinguables par les daltoniens ; le sexe est en plus signalé par le trait (tirets = garçons).
const COULEURS_SEXE = { F: '#b5552b', M: '#2f5f8a' }
const PALETTE = ['#b5552b', '#2f5f8a', '#2b7a5c', '#8a4f8f']
const MAX_COMPARAISON = 3

const index = ref([])
const prenom = ref(null)
const autresGraphies = ref([])
const series = ref(null)
const meta = ref(null)
const mesure = ref('valeur')
const etat = ref('chargement') // chargement | ok | introuvable | erreur
const compares = ref([]) // [{ prenom, series, sexe }]
const rechercheComparaison = ref('')

async function charger() {
  etat.value = 'chargement'
  compares.value = []
  try {
    const [idx, m] = await Promise.all([chargerIndex(), chargerMeta()])
    index.value = idx
    meta.value = m
    const p = idx.find((x) => x.id === props.id)
    if (!p) { etat.value = 'introuvable'; return }
    prenom.value = p
    autresGraphies.value = idx.filter((x) => x.norm === p.norm && x.id !== p.id)
    series.value = await chargerSeries(p)
    etat.value = 'ok'
    document.title = `${p.affichage} — Prénoscope`
  } catch {
    etat.value = 'erreur'
  }
}
watch(() => props.id, charger, { immediate: true })

const sexes = computed(() => ['F', 'M'].filter((s) => series.value?.[s]))

const blocs = computed(() => sexes.value.map((sexe) => ({
  sexe,
  ind: indicateurs(series.value[sexe], sexe, meta.value.naissances, meta.value.nb_publies, meta.value.regles,
    meta.value.annee_max),
  tendances: ORDRE_TENDANCES.filter((t) => series.value.tendances?.[sexe]?.includes(t)),
  vagues: series.value.vagues?.[sexe] ?? [],
})))

const partMinoritaire = computed(() => {
  const p = prenom.value
  return p && p.total ? Math.min(p.totalF, p.totalM) / p.total : 0
})

// --- Comparaison ---
const sexePrincipal = (p) => (p.sexe === 'X' ? (p.totalF >= p.totalM ? 'F' : 'M') : p.sexe)
const suggestions = computed(() => {
  const t = normaliser(rechercheComparaison.value.trim())
  if (t.length < 2) return []
  const pris = new Set([props.id, ...compares.value.map((c) => c.prenom.id)])
  return index.value.filter((p) => p.norm.startsWith(t) && !pris.has(p.id)).slice(0, 6)
})
async function comparer(p) {
  rechercheComparaison.value = ''
  if (compares.value.length >= MAX_COMPARAISON) return
  const s = await chargerSeries(p)
  compares.value = [...compares.value, { prenom: p, series: s, sexe: sexePrincipal(p) }]
}
function retirer(id) { compares.value = compares.value.filter((c) => c.prenom.id !== id) }

const courbes = computed(() => {
  if (!series.value) return []
  const seul = !compares.value.length
  const principales = sexes.value.map((s) => ({
    nom: seul ? NOMS[s] : `${prenom.value.affichage}${sexes.value.length > 1 ? ` (${NOMS[s].toLowerCase()})` : ''}`,
    sexe: s, couleur: seul ? COULEURS_SEXE[s] : PALETTE[0], tirets: s === 'M', points: series.value[s],
  }))
  return [...principales, ...compares.value.map((c, i) => ({
    nom: c.prenom.affichage, sexe: c.sexe, couleur: PALETTE[i + 1], tirets: c.sexe === 'M', points: c.series[c.sexe] || [],
  }))]
})

const pct = (x) => `${x > 0 ? '+' : ''}${(x * 100).toLocaleString('fr-FR', { maximumFractionDigits: 0 })} %`
const pourMille = (x) => `${x.toLocaleString('fr-FR', { maximumFractionDigits: 2 })} ‰`
</script>

<template>
  <a href="#/" class="retour" @click.prevent="retour">← Retour</a>

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
        <RouterLink :to="{ name: 'methode', hash: '#qualite' }" :class="['badge', 'qualite', 'q-' + prenom.qualite]"
                    title="Niveau de documentation de la fiche (voir la méthode)">{{ LIBELLES_QUALITE[prenom.qualite] }}</RouterLink>
        <span class="doux">
          {{ prenom.lettres }} lettres<template v-if="prenom.compose"> · composé</template>
          · graphie Insee : {{ prenom.id.toUpperCase() }}
        </span>
      </p>
      <p class="doux petit">
        Environ {{ prenom.total.toLocaleString('fr-FR') }} naissances en France entre
        {{ prenom.premiereAnnee }} et {{ prenom.derniereAnnee }}<template v-if="prenom.totalF && prenom.totalM">
          (filles : {{ environ(prenom.totalF) }}, garçons : {{ environ(prenom.totalM) }},
          soit {{ pourcentage(partMinoritaire) }}
          pour le sexe le moins représenté ; « mixte » à partir de {{ meta.regles.seuil_mixte * 100 }} %)</template>.
      </p>
      <ul v-if="blocs.some((b) => b.tendances.length)" class="tendances" aria-label="Tendances">
        <template v-for="b in blocs" :key="b.sexe">
          <li v-for="t in b.tendances" :key="b.sexe + t">
            <RouterLink :to="{ name: 'tendances', query: { categorie: t } }" class="etiquette"
                        :title="definitionTendance(t, meta.regles.tendances, meta.annee_max)">
              {{ LIBELLES_TENDANCES[t] }}<template v-if="sexes.length > 1"> ({{ NOMS[b.sexe].toLowerCase() }})</template>
            </RouterLink>
          </li>
        </template>
      </ul>
    </header>

    <EncyclopediePrenom :prenom="prenom" />

    <section class="carte" aria-labelledby="titre-courbe">
      <div class="titre-section">
        <h2 id="titre-courbe">Popularité en France depuis {{ meta.annee_min }}</h2>
        <div class="segments" role="group" aria-label="Mesure affichée">
          <button :aria-pressed="mesure === 'valeur'" @click="mesure = 'valeur'">Naissances</button>
          <button :aria-pressed="mesure === 'frequence'" @click="mesure = 'frequence'">Pour 1 000</button>
          <button :aria-pressed="mesure === 'rang'" @click="mesure = 'rang'">Rang</button>
        </div>
      </div>
      <CourbeNationale :courbes="courbes" :mesure="mesure" :naissances="meta.naissances"
                       :annee-min="meta.annee_min" :annee-max="meta.annee_max" />
      <p class="doux petit note">
        <template v-if="mesure === 'valeur'">Effectifs arrondis par l'Insee au multiple de 5 : ce sont des ordres de grandeur.</template>
        <template v-else-if="mesure === 'frequence'">
          Naissances du prénom pour 1 000 naissances du même sexe (série officielle Insee de l'état civil).
          Calculé à partir de {{ meta.regles.annee_debut_frequences }} seulement : avant, le fichier des prénoms ne recense
          qu'une partie des naissances. Jusqu'en {{ meta.regles.annee_debut_france_entiere - 1 }}, le dénominateur ne couvre
          que la métropole (légère surestimation, de l'ordre de 2 à 3 %).
          <RouterLink to="/methode">En savoir plus</RouterLink>
        </template>
        <template v-else>Rang officiel Insee parmi les prénoms du même sexe (1 = le plus donné), échelle logarithmique.</template>
        Une année sans point signifie que le prénom n'apparaît pas dans le fichier cette année-là
        (effectif nul ou trop faible après arrondi), pas forcément zéro naissance.
      </p>

      <div class="comparaison">
        <label class="champ-comparaison">
          <span>Comparer avec un autre prénom</span>
          <input v-model="rechercheComparaison" type="search" autocomplete="off" spellcheck="false"
                 :disabled="compares.length >= MAX_COMPARAISON"
                 :placeholder="compares.length >= MAX_COMPARAISON ? `${MAX_COMPARAISON} prénoms au maximum` : 'ex. jules'" />
        </label>
        <ul v-if="suggestions.length" class="suggestions" aria-label="Suggestions">
          <li v-for="s in suggestions" :key="s.id">
            <button class="bouton petit" @click="comparer(s)">+ {{ s.affichage }}</button>
          </li>
        </ul>
        <ul v-if="compares.length" class="compares" aria-label="Prénoms comparés">
          <li v-for="c in compares" :key="c.prenom.id">
            <button class="bouton petit" :aria-label="`Retirer ${c.prenom.affichage} de la comparaison`"
                    @click="retirer(c.prenom.id)">{{ c.prenom.affichage }} ✕</button>
          </li>
        </ul>
        <p v-if="compares.length" class="doux petit">
          Pour chaque prénom comparé, le sexe le plus fréquent est affiché (traits pleins : filles ; tirets : garçons).
        </p>
      </div>
    </section>

    <section class="carte" aria-labelledby="titre-chiffres">
      <h2 id="titre-chiffres">Chiffres clés</h2>
      <div class="blocs">
        <dl v-for="b in blocs" :key="b.sexe" class="bloc">
          <dt class="bloc-titre">{{ NOMS[b.sexe] }}</dt>
          <dd v-if="b.ind.derniere">
            En {{ b.ind.derniere.annee }} : <strong>{{ ordinal(b.ind.derniere.rang).nombre }}<sup>{{ ordinal(b.ind.derniere.rang).suffixe }}</sup></strong>
            sur {{ b.ind.derniere.nb_publies.toLocaleString('fr-FR') }} prénoms publiés,
            {{ environ(b.ind.derniere.valeur) }} naissances<template v-if="b.ind.derniere.frequence != null">
            ({{ pourMille(b.ind.derniere.frequence) }})</template>.
          </dd>
          <dd v-else>Absent du fichier en {{ meta.annee_max }} (effectif trop faible pour être publié).</dd>
          <dd>Meilleur rang : <strong>{{ ordinal(b.ind.meilleur_rang[1]).nombre }}<sup>{{ ordinal(b.ind.meilleur_rang[1]).suffixe }}</sup></strong> en {{ b.ind.meilleur_rang[0] }}</dd>
          <dd>Année la plus forte en naissances : {{ b.ind.record_effectif[0] }} ({{ environ(b.ind.record_effectif[1]) }})</dd>
          <dd v-if="b.ind.record_frequence">
            Fréquence record (depuis {{ meta.regles.annee_debut_frequences }}) : {{ b.ind.record_frequence[0] }}
            ({{ pourMille(b.ind.record_frequence[1]) }})
          </dd>
          <dd class="evolutions">
            Évolution de la fréquence :
            <ul>
              <li v-for="(e, k) in b.ind.evolutions" :key="k">
                sur {{ k }} ans ({{ e.avant[0] }}–{{ e.avant[1] }} → {{ e.apres[0] }}–{{ e.apres[1] }}) :
                <strong v-if="e.variation != null">{{ pct(e.variation) }}</strong>
                <span v-else class="doux">non calculée (moins de {{ meta.regles.evolution_min }} naissances par an)</span>
              </li>
            </ul>
          </dd>
          <dd v-if="b.vagues.length" class="doux">
            Sommet{{ b.vagues.length > 1 ? 's' : '' }} de popularité :
            {{ b.vagues.map((v) => `${v[0]} (rang ≈ ${v[1]})`).join(', ') }}
          </dd>
          <dd class="doux">Présent {{ b.ind.nb_annees }} année{{ b.ind.nb_annees > 1 ? 's' : '' }} sur {{ meta.annee_max - meta.annee_min + 1 }}</dd>
        </dl>
      </div>
      <p class="doux petit">
        Évolutions : fréquence moyenne sur 3 ans, comparée à la même moyenne 5, 10 ou 20 ans plus tôt.
        <RouterLink to="/methode">Définitions</RouterLink>
      </p>
    </section>

    <GeographiePrenom :prenom="prenom" :meta="meta" />

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
      <p v-if="prenom.qualite === 'm'">
        Fiche <strong>minimale</strong> : statistiques de l'Insee uniquement. Aucune origine, étymologie ou personnalité
        sourcée n'a été trouvée pour cette graphie exacte ; rien n'est affiché sans source.
      </p>
      <p v-else-if="prenom.qualite === 'p'">
        Fiche <strong>partielle</strong> : statistiques de l'Insee et une partie seulement des informations
        encyclopédiques (étymologie, variantes, personnalités), chacune avec sa source.
      </p>
      <p v-else>
        Fiche <strong>complète</strong> : statistiques de l'Insee, étymologie sourcée, variantes et personnalités.
      </p>
      <p>Aucune anecdote n'est encore publiée : aucune source ouverte et fiable n'a été retenue pour ce type de contenu.</p>
      <p>
        Sources : {{ meta.source.organisme }}, {{ meta.source.titre }} ; Insee, statistiques de l'état civil (naissances par sexe) ;
        IGN, contours administratifs — {{ meta.source.licence }} ; Wikidata (CC0) ; Wiktionnaire (CC BY-SA 4.0, textes
        signalés comme tels). <RouterLink to="/methode">Méthode et sources</RouterLink>
      </p>
    </section>
  </article>
</template>

<style scoped>
.retour { display: inline-block; margin-bottom: 16px; text-decoration: none; }
.etat { padding: 24px 0; }
.fiche { display: grid; gap: 16px; }
.entete h1 { font-size: 2.6rem; margin: 0 0 8px; color: var(--accent); }
.sous-titre { display: flex; flex-wrap: wrap; gap: 8px 12px; align-items: center; margin: 0 0 8px; }
.qualite { text-decoration: none; color: var(--texte-doux); }
.qualite.q-c { color: #2b7a5c; }
.qualite.q-p { color: #8a6a1f; }
.tendances { list-style: none; padding: 0; margin: 10px 0 0; display: flex; flex-wrap: wrap; gap: 8px; }
.etiquette {
  display: inline-block; padding: 3px 12px; border-radius: 999px; background: var(--accent-fond);
  color: var(--accent); font-weight: 600; font-size: 0.85rem; text-decoration: none;
}
.titre-section { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 8px; }
h2 { font-size: 1.25rem; margin: 0 0 8px; }
.h-petit { font-size: 1rem; }
.segments { display: flex; gap: 4px; background: var(--surface-douce); padding: 3px; border-radius: 999px; }
.segments button { border: 0; background: transparent; padding: 5px 12px; border-radius: 999px; cursor: pointer; }
.segments button[aria-pressed='true'] { background: var(--surface); color: var(--accent); font-weight: 600; box-shadow: var(--ombre); }
.note { margin: 4px 0 12px; }
.comparaison { border-top: 1px solid var(--bordure); padding-top: 12px; display: grid; gap: 8px; }
.champ-comparaison { display: grid; gap: 4px; max-width: 360px; }
.champ-comparaison span { font-size: 0.85rem; font-weight: 600; color: var(--texte-doux); }
.champ-comparaison input { padding: 8px 12px; border: 1px solid var(--bordure); border-radius: 10px; background: var(--fond); }
.suggestions, .compares { list-style: none; padding: 0; margin: 0; display: flex; flex-wrap: wrap; gap: 6px; }
.compares .bouton { background: var(--accent-fond); border-color: var(--accent); }
.blocs { display: grid; gap: 12px; }
@media (min-width: 720px) { .blocs { grid-template-columns: 1fr 1fr; } }
.bloc { background: var(--fond); border-radius: 10px; padding: 12px 14px; margin: 0; }
.bloc-titre { font-weight: 700; margin-bottom: 4px; }
.bloc dd { margin: 0 0 3px; }
.evolutions ul { margin: 2px 0 0; padding-left: 18px; }
.graphies { list-style: none; padding: 0; margin: 0; display: flex; flex-wrap: wrap; gap: 8px 18px; }
.graphies a { font-family: var(--serif); font-size: 1.1rem; }
</style>
