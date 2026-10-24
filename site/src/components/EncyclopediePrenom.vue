<script setup>
// Sections encyclopédiques d'une fiche : origine et étymologie, prononciation, variantes,
// personnalités, liens. Chaque information affiche sa source ; rien n'est complété ou deviné.
import { ref, computed, watch } from 'vue'
import { chargerEncyclo, chargerWiktionnaire } from '../lib/dataLoader.js'
import { regrouperVariantes, LIBELLES_VARIANTES } from '../lib/encyclopedie.js'

const props = defineProps({ prenom: { type: Object, required: true } })

const etat = ref('chargement')
const wd = ref({})
const wikt = ref({})
const toutesTraductions = ref(false)

async function charger() {
  etat.value = 'chargement'
  const [a, b] = await Promise.all([chargerEncyclo(props.prenom), chargerWiktionnaire(props.prenom)])
  wd.value = a
  wikt.value = b
  etat.value = 'ok'
}
watch(() => props.prenom.id, charger, { immediate: true })

const entrees = computed(() => wikt.value.entrees ?? [])
const etymologies = computed(() => entrees.value.filter((e) => e.etymologie))
const origines = computed(() => [...new Set(entrees.value.flatMap((e) => e.origines))])
const prononciations = computed(() => [...new Set(entrees.value.flatMap((e) => e.api))])
const groupes = computed(() => regrouperVariantes(wikt.value.variantes ?? [], wd.value.variantes ?? [], props.prenom.id))
const personnalites = computed(() => wd.value.personnalites ?? [])
const elementsWd = computed(() => wd.value.wikidata ?? [])
const ambigu = computed(() => elementsWd.value.some((e) => e.statut === 'ambigu'))
const articles = computed(() => [...new Set(elementsWd.value.map((e) => e.article).filter(Boolean))])
const rien = computed(() => !entrees.value.length && !elementsWd.value.length)

const dates = (p) => {
  if (p.naissance == null && p.deces == null) return ''
  if (p.deces == null) return `naissance en ${p.naissance}`
  return `${p.naissance ?? '?'}–${p.deces}`
}
const nomPage = (url) => decodeURIComponent(url.split('/wiki/')[1] ?? '').replaceAll('_', ' ')
</script>

<template>
  <div v-if="etat === 'chargement'" class="carte doux" role="status">Chargement des informations encyclopédiques…</div>
  <section v-else-if="rien" class="carte doux petit" aria-label="Informations encyclopédiques">
    <p>
      Aucune information encyclopédique sourcée n'a été trouvée pour cette graphie exacte, ni dans le Wiktionnaire
      ni dans Wikidata. Prénoscope n'affiche pas d'origine ni de signification sans source.
    </p>
  </section>

  <template v-else>
    <section v-if="etymologies.length || origines.length || prononciations.length" class="carte" aria-labelledby="titre-origine">
      <h2 id="titre-origine">Origine et étymologie</h2>
      <p v-if="prononciations.length" class="prononciation">
        Prononciation : <span class="api">{{ prononciations.join(' ou ') }}</span>
        <span class="doux petit">(alphabet phonétique international)</span>
      </p>
      <p v-if="origines.length">
        Langue d'origine : <strong>{{ origines.join(', ') }}</strong>
      </p>
      <blockquote v-for="e in etymologies" :key="e.url + e.section" class="citation">
        <p v-for="(ligne, i) in e.etymologie.split('\n')" :key="i">{{ ligne }}</p>
        <footer class="doux petit">
          — Wiktionnaire, page <a :href="e.url" rel="noopener">« {{ e.mot }} »</a><template v-if="etymologies.length > 1"> ({{ e.section }})</template>,
          texte sous licence <a href="https://creativecommons.org/licenses/by-sa/4.0/deed.fr" rel="license noopener">CC BY-SA 4.0</a>
          (<a :href="e.url + '?action=history'" rel="noopener">auteurs</a>). Repris tel quel, non relu par Prénoscope.
        </footer>
      </blockquote>
      <p v-if="!etymologies.length && entrees.length" class="doux petit">
        Le Wiktionnaire décrit ce prénom mais ne donne pas son étymologie.
        <a :href="entrees[0].url" rel="noopener">Voir la page</a>
      </p>
    </section>

    <section v-if="groupes.length" class="carte" aria-labelledby="titre-variantes">
      <h2 id="titre-variantes">Variantes et formes apparentées</h2>
      <dl class="variantes">
        <template v-for="g in groupes" :key="g.type">
          <dt>{{ LIBELLES_VARIANTES[g.type] }}</dt>
          <dd>
            <ul>
              <li v-for="v in (g.type === 'traduction' && !toutesTraductions ? g.items.slice(0, 24) : g.items)"
                  :key="v.libelle + (v.langue ?? '')">
                <RouterLink v-if="v.id" :to="{ name: 'fiche', params: { id: v.id } }">{{ v.libelle }}</RouterLink>
                <span v-else>{{ v.libelle }}</span>
                <span v-if="v.langue" class="doux petit"> ({{ v.langue }})</span>
              </li>
            </ul>
            <button v-if="g.type === 'traduction' && g.items.length > 24 && !toutesTraductions"
                    class="bouton petit" @click="toutesTraductions = true">Voir les {{ g.items.length }} formes</button>
          </dd>
        </template>
      </dl>
      <p class="doux petit">
        Liens : prénoms présents dans le fichier de l'Insee (graphie exacte). Sources : Wiktionnaire (CC BY-SA 4.0) et
        Wikidata (« réputé identique à », « équivalent dans l'autre genre », CC0).
      </p>
    </section>

    <section v-if="wd.langues?.length" class="carte" aria-labelledby="titre-langues">
      <h2 id="titre-langues">Langues d'usage</h2>
      <p>{{ wd.langues.join(', ') }}</p>
      <p class="doux petit">
        Langues dans lesquelles Wikidata indique que ce prénom est employé (propriété « langue de l'œuvre ou du nom ») :
        ce n'est pas nécessairement sa langue d'origine.
      </p>
    </section>

    <section v-if="personnalites.length" class="carte" aria-labelledby="titre-personnalites">
      <h2 id="titre-personnalites">Personnalités</h2>
      <ul class="personnalites">
        <li v-for="p in personnalites" :key="p.qid">
          <a :href="p.url" rel="noopener" class="nom-perso">{{ p.nom }}</a>
          <span v-if="dates(p)" class="doux"> ({{ dates(p) }})</span>
          <p v-if="p.presentation" class="presentation">{{ p.presentation }}</p>
          <p class="doux petit">
            <template v-if="p.domaines.length">{{ p.domaines.join(', ') }} · </template>article dans {{ p.liens }} projets Wikimédia
          </p>
        </li>
      </ul>
      <p class="doux petit">
        Sélection automatique et explicable : personnes dont c'est le prénom (le premier, quand Wikidata indique
        l'ordre), ayant un article sur Wikipédia en français ; classées par nombre de projets Wikimédia (Wikipédia
        dans d'autres langues, etc.) qui leur consacrent un article. Présentations : descriptions de Wikidata (CC0).
      </p>
    </section>

    <section class="carte doux petit" aria-labelledby="titre-liens">
      <h2 id="titre-liens" class="h-petit">Pour aller plus loin</h2>
      <ul class="liens">
        <li v-for="a in articles" :key="a"><a :href="a" rel="noopener">Wikipédia : « {{ nomPage(a) }} »</a></li>
        <li v-for="e in entrees" :key="'w' + e.url + e.section"><a :href="e.url" rel="noopener">Wiktionnaire : « {{ e.mot }} »</a></li>
        <li v-for="e in elementsWd" :key="e.qid">
          <a :href="`https://www.wikidata.org/wiki/${e.qid}`" rel="noopener">Wikidata : {{ e.libelle }} ({{ e.qid }})</a>
        </li>
      </ul>
      <p v-if="ambigu">
        Plusieurs éléments Wikidata de même graphie correspondent à ce prénom : leurs informations sont réunies ici.
      </p>
    </section>
  </template>
</template>

<style scoped>
h2 { font-size: 1.25rem; margin: 0 0 8px; }
.h-petit { font-size: 1rem; }
.carte + .carte { margin-top: 0; }
.prononciation .api { font-family: 'Charis SIL', 'Doulos SIL', 'Gentium', serif; font-size: 1.1rem; }
.citation { margin: 10px 0; padding: 10px 14px; border-left: 3px solid var(--accent); background: var(--fond); border-radius: 0 10px 10px 0; }
.citation p { margin: 0 0 6px; }
.citation footer { margin-top: 4px; }
.variantes dt { font-weight: 700; margin-top: 10px; }
.variantes dd { margin: 4px 0 0; }
.variantes ul { list-style: none; padding: 0; margin: 0 0 6px; display: flex; flex-wrap: wrap; gap: 4px 14px; }
.personnalites { list-style: none; padding: 0; margin: 0; display: grid; gap: 10px; }
@media (min-width: 720px) { .personnalites { grid-template-columns: 1fr 1fr; } }
.personnalites li { background: var(--fond); border-radius: 10px; padding: 10px 12px; }
.nom-perso { font-family: var(--serif); font-size: 1.1rem; font-weight: 600; text-decoration: none; }
.presentation { margin: 2px 0; }
.personnalites .petit { margin: 0; }
.liens { margin: 0; padding-left: 18px; }
</style>
