<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, MarkLineComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { chargerMeta, chargerCouverture } from '../lib/dataLoader.js'
import { ORDRE_TENDANCES, LIBELLES_TENDANCES, definitionTendance } from '../lib/tendances.js'

echarts.use([LineChart, GridComponent, TooltipComponent, LegendComponent, MarkLineComponent, CanvasRenderer])

const meta = ref(null)
const etat = ref('chargement')
const conteneur = ref(null)
let graphique = null

async function charger() {
  try {
    const [m, c] = await Promise.all([chargerMeta(), chargerCouverture()])
    meta.value = m
    plages.value = calculerPlages(c, m.regles)
    etat.value = 'ok'
    await nextTick()
    dessiner(c)
  } catch {
    etat.value = 'erreur'
  }
}

// Plages de couverture (min–max, en %) par période, calculées sur les données publiées.
const plages = ref(null)
function calculerPlages(couverture, regles) {
  const col = Object.fromEntries(couverture.colonnes.map((n, i) => [n, i]))
  const plage = (test) => {
    const r = couverture.lignes.filter((l) => l[col.ratio] != null && test(l[col.annee])).map((l) => l[col.ratio] * 100)
    return [Math.floor(Math.min(...r)), Math.ceil(Math.max(...r))]
  }
  return {
    avant: plage((a) => a < regles.annee_debut_frequences),
    metropole: plage((a) => a >= regles.annee_debut_frequences && a < regles.annee_debut_france_entiere),
    france: plage((a) => a >= regles.annee_debut_france_entiere),
  }
}

function dessiner(couverture) {
  const col = Object.fromEntries(couverture.colonnes.map((n, i) => [n, i]))
  const lignes = couverture.lignes.filter((l) => l[col.ratio] != null)
  const annees = [...new Set(lignes.map((l) => l[col.annee]))]
  const serie = (s) => annees.map((a) => {
    const l = lignes.find((x) => x[col.annee] === a && x[col.sexe] === s)
    return l ? Math.round(l[col.ratio] * 1000) / 10 : null
  })
  graphique = echarts.init(conteneur.value)
  graphique.setOption({
    grid: { left: 48, right: 16, top: 36, bottom: 32 },
    legend: { top: 0 },
    tooltip: { trigger: 'axis', valueFormatter: (v) => (v == null ? '—' : `${v.toLocaleString('fr-FR')} %`) },
    xAxis: { type: 'category', data: annees, boundaryGap: false },
    yAxis: { type: 'value', min: 30, max: 110, axisLabel: { formatter: '{value} %' } },
    series: [
      { name: 'Filles', type: 'line', data: serie('F'), showSymbol: false, lineStyle: { color: '#b5552b', width: 2.5 },
        itemStyle: { color: '#b5552b' },
        markLine: { silent: true, symbol: 'none', lineStyle: { color: '#6b6157', type: 'dotted' },
          data: [{ yAxis: 100 }, { xAxis: String(meta.value.regles.annee_debut_frequences) },
            { xAxis: String(meta.value.regles.annee_debut_france_entiere) }], label: { show: false } } },
      { name: 'Garçons', type: 'line', data: serie('M'), showSymbol: false,
        lineStyle: { color: '#2f5f8a', width: 2.5, type: [6, 3] }, itemStyle: { color: '#2f5f8a' } },
    ],
  })
}

const redimensionner = () => graphique?.resize()
onMounted(() => { charger(); window.addEventListener('resize', redimensionner) })
onBeforeUnmount(() => { window.removeEventListener('resize', redimensionner); graphique?.dispose() })
</script>

<template>
  <article class="methode">
    <h1 class="titre">Méthode et sources</h1>
    <p class="doux intro">Ce que disent les chiffres de Prénoscope, et ce qu'ils ne disent pas.</p>

    <div v-if="etat === 'chargement'" role="status">Chargement…</div>
    <div v-else-if="etat === 'erreur'" role="alert">Les informations n'ont pas pu être chargées.</div>
    <template v-else>
      <section class="carte">
        <h2>Les données de l'Insee</h2>
        <ul>
          <li>Le <strong>fichier des prénoms</strong> recense le premier prénom des enfants nés en France depuis
            {{ meta.annee_min }}, par sexe, année, région et département de naissance.</li>
          <li>Les <strong>effectifs sont arrondis</strong> par l'Insee au multiple de 5 le plus proche : Prénoscope écrit
            toujours « environ ». Un prénom donné 1 ou 2 fois dans l'année (arrondi à 0) n'apparaît pas.</li>
          <li>Les <strong>rangs</strong> sont ceux de l'Insee, calculés sur les effectifs exacts. Ils ne sont jamais recalculés.
            Les classements par décennie, eux, sont calculés par Prénoscope et signalés comme tels.</li>
          <li>Une année sans donnée n'est pas une année sans naissance : elle est laissée vide sur les courbes.</li>
          <li>La géographie est celle d'aujourd'hui (un enfant né en 1949 à Issy-les-Moulineaux est compté dans les
            Hauts-de-Seine) et correspond au <strong>lieu de naissance</strong>, pas à l'origine du prénom. Mayotte n'est
            incluse qu'à partir de 2012.</li>
        </ul>
      </section>

      <section class="carte">
        <h2>Fréquence pour 1 000 naissances</h2>
        <p>
          Le fichier des prénoms ne donne pas le nombre total de naissances. Prénoscope utilise la série officielle de
          l'état civil (Insee, tableau T35 : naissances vivantes par sexe). La courbe ci-dessous compare, chaque année, la somme
          des effectifs du fichier des prénoms à ces naissances officielles.
        </p>
        <div ref="conteneur" class="courbe" role="img"
             aria-label="Part des naissances officielles retrouvée dans le fichier des prénoms, par année et par sexe"></div>
        <ul>
          <li><strong>Avant {{ meta.regles.annee_debut_frequences }}</strong>, le fichier ne retrouve qu'une partie des naissances
            (de {{ plages.avant[0] }} à {{ plages.avant[1] }} % selon l'année et le sexe) : les fréquences n'y sont donc pas
            calculées ; seuls les effectifs et les rangs sont montrés.</li>
          <li><strong>De {{ meta.regles.annee_debut_frequences }} à {{ meta.regles.annee_debut_france_entiere - 1 }}</strong>, la série
            officielle ne couvre que la métropole alors que le fichier inclut l'outre-mer : le rapport atteint
            {{ plages.metropole[0] }} à {{ plages.metropole[1] }} %, et la fréquence est donc légèrement surestimée.</li>
          <li><strong>Depuis {{ meta.regles.annee_debut_france_entiere }}</strong>, la série couvre la France entière ; le fichier
            en retrouve {{ plages.france[0] }} à {{ plages.france[1] }} % (les prénoms trop rares ne sont pas publiés).</li>
        </ul>
      </section>

      <section class="carte">
        <h2>Indicateurs d'une fiche</h2>
        <ul>
          <li><strong>Évolution sur 5, 10 ou 20 ans</strong> : fréquence moyenne des 3 dernières années comparée à la même
            moyenne 5, 10 ou 20 ans plus tôt ; non calculée en dessous de {{ meta.regles.evolution_min }} naissances par an.</li>
          <li><strong>Popularité relative d'une zone (indice)</strong> : part du prénom parmi les naissances publiées de la zone,
            divisée par sa part dans l'ensemble des zones du même découpage, × 100. Non calculé sous
            {{ meta.regles.geo_min_indice }} naissances.</li>
          <li><strong>Mixte</strong> : prénom dont le sexe le moins représenté atteint au moins {{ meta.regles.seuil_mixte * 100 }} %
            des naissances depuis {{ meta.annee_min }}.</li>
        </ul>
      </section>

      <section class="carte">
        <h2>Tendances</h2>
        <dl class="definitions">
          <template v-for="c in ORDRE_TENDANCES" :key="c">
            <dt>{{ LIBELLES_TENDANCES[c] }}</dt>
            <dd>{{ definitionTendance(c, meta.regles.tendances, meta.annee_max) }}</dd>
          </template>
        </dl>
        <p class="doux petit">
          Fréquences : naissances pour 1 000 naissances du même sexe. Une année absente compte comme « au plus 2 naissances ».
          Ces catégories décrivent le passé ; elles ne prédisent pas l'avenir.
        </p>
      </section>

      <section class="carte">
        <h2>Sources et licences</h2>
        <ul>
          <li v-for="s in meta.sources" :key="s.id">
            <a :href="s.url">{{ s.organisme }} — {{ s.titre }}</a>
            <span class="doux"> ({{ s.licence }} ; publié {{ s.publication }}, récupéré le
              {{ new Date(s.date_recuperation).toLocaleDateString('fr-FR') }})</span>
          </li>
        </ul>
      </section>
    </template>
  </article>
</template>

<style scoped>
.methode { display: grid; gap: 16px; }
.titre { font-size: 2rem; margin: 0; }
.intro { margin: 0; }
h2 { font-size: 1.25rem; margin: 0 0 8px; }
ul { padding-left: 20px; margin: 8px 0; }
li { margin-bottom: 6px; }
.courbe { width: 100%; height: 300px; }
.definitions dt { font-weight: 700; margin-top: 10px; }
.definitions dd { margin: 2px 0 0; }
</style>
