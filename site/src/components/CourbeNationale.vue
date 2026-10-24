<script setup>
// Courbes nationales : effectif arrondi, fréquence pour 1 000 naissances (1946+) ou rang officiel.
// Une année sans ligne dans le fichier Insee est laissée vide (trou dans la courbe), jamais à zéro.
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { frequence } from '../lib/indicateurs.js'

echarts.use([LineChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer])

const props = defineProps({
  // [{ nom, sexe, couleur, tirets, points: [[annee, valeur, rang]…] }]
  courbes: { type: Array, required: true },
  mesure: { type: String, default: 'valeur' }, // valeur | frequence | rang
  naissances: { type: Object, default: () => ({}) },
  anneeMin: { type: Number, default: 1900 },
  anneeMax: { type: Number, default: 2025 },
})

const conteneur = ref(null)
let graphique = null

const formats = {
  valeur: (v) => `environ ${v.toLocaleString('fr-FR')}`,
  frequence: (v) => `${v.toLocaleString('fr-FR', { maximumFractionDigits: 2 })} ‰`,
  rang: (v) => `rang ${v.toLocaleString('fr-FR')}`,
}

function options() {
  const annees = []
  for (let a = props.anneeMin; a <= props.anneeMax; a++) annees.push(a)
  const series = props.courbes.map((c) => {
    const parAnnee = new Map(c.points.map((p) => [p[0], p]))
    const donnee = (a) => {
      const p = parAnnee.get(a)
      if (!p) return null
      if (props.mesure === 'rang') return p[2]
      if (props.mesure === 'frequence') {
        const f = frequence(p[1], a, c.sexe, props.naissances)
        return f == null ? null : Number(f.toFixed(3))
      }
      return p[1]
    }
    return {
      name: c.nom,
      type: 'line',
      data: annees.map(donnee),
      connectNulls: false,
      showSymbol: false,
      lineStyle: { width: 2.5, color: c.couleur, type: c.tirets ? [6, 3] : 'solid' },
      itemStyle: { color: c.couleur },
    }
  })
  return {
    animationDuration: 400,
    grid: { left: 56, right: 16, top: 36, bottom: 32 },
    legend: { top: 0, type: 'scroll', textStyle: { color: '#2b2620' } },
    tooltip: {
      trigger: 'axis',
      valueFormatter: (v) => (v == null ? (props.mesure === 'frequence' ? 'non calculée' : 'aucune ligne Insee')
        : formats[props.mesure](v)),
    },
    xAxis: { type: 'category', data: annees, boundaryGap: false, axisLabel: { color: '#6b6157' } },
    yAxis: {
      type: props.mesure === 'rang' ? 'log' : 'value',
      inverse: props.mesure === 'rang',
      min: props.mesure === 'rang' ? 1 : 0,
      axisLabel: { color: '#6b6157', formatter: (v) => v.toLocaleString('fr-FR') },
      splitLine: { lineStyle: { color: '#eee6da' } },
    },
    series,
  }
}

function redimensionner() { graphique?.resize() }

onMounted(() => {
  graphique = echarts.init(conteneur.value)
  graphique.setOption(options())
  window.addEventListener('resize', redimensionner)
})
watch(() => [props.courbes, props.mesure], () => graphique?.setOption(options(), true), { deep: true })
onBeforeUnmount(() => {
  window.removeEventListener('resize', redimensionner)
  graphique?.dispose()
})

const libelles = { valeur: 'des effectifs arrondis', frequence: 'de la fréquence pour 1 000 naissances', rang: 'du rang officiel' }
</script>

<template>
  <div ref="conteneur" class="courbe" role="img"
       :aria-label="`Courbe ${libelles[mesure]} par année, France entière : ${courbes.map((c) => c.nom).join(', ')}`"></div>
</template>

<style scoped>
.courbe { width: 100%; height: 340px; }
</style>
