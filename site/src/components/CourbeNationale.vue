<script setup>
// Courbe nationale par sexe : effectif arrondi ou rang officiel, 1900 → dernière année.
// Une année sans ligne dans le fichier Insee est laissée vide (trou dans la courbe), jamais à zéro.
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([LineChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer])

const props = defineProps({
  series: { type: Object, required: true }, // { F: [[annee, valeur, rang]…], M: […] }
  mesure: { type: String, default: 'valeur' }, // valeur | rang
  anneeMin: { type: Number, default: 1900 },
  anneeMax: { type: Number, default: 2025 },
})

const COULEURS = { F: '#b5552b', M: '#2f5f8a' }
const NOMS = { F: 'Filles', M: 'Garçons' }
const conteneur = ref(null)
let graphique = null

function options() {
  const annees = []
  for (let a = props.anneeMin; a <= props.anneeMax; a++) annees.push(a)
  const colonne = props.mesure === 'rang' ? 2 : 1
  const series = ['F', 'M'].filter((s) => props.series[s]).map((sexe) => {
    const points = props.series[sexe]
    const parAnnee = new Map(points.map((p) => [p[0], p[colonne]]))
    return {
      name: NOMS[sexe],
      type: 'line',
      data: annees.map((a) => parAnnee.get(a) ?? null),
      connectNulls: false,
      showSymbol: false,
      smooth: false,
      lineStyle: { width: 2.5, color: COULEURS[sexe], type: sexe === 'M' ? [6, 3] : 'solid' },
      itemStyle: { color: COULEURS[sexe] },
    }
  })
  return {
    animationDuration: 400,
    grid: { left: 56, right: 16, top: 36, bottom: 32 },
    legend: { top: 0, textStyle: { color: '#2b2620' } },
    tooltip: {
      trigger: 'axis',
      valueFormatter: (v) => v == null ? 'aucune ligne Insee'
        : props.mesure === 'rang' ? `rang ${v.toLocaleString('fr-FR')}` : `environ ${v.toLocaleString('fr-FR')}`,
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
watch(() => [props.series, props.mesure], () => graphique?.setOption(options(), true))
onBeforeUnmount(() => {
  window.removeEventListener('resize', redimensionner)
  graphique?.dispose()
})
</script>

<template>
  <div ref="conteneur" class="courbe" role="img"
       :aria-label="`Courbe ${mesure === 'rang' ? 'du rang officiel' : 'des effectifs arrondis'} par année, France entière`"></div>
</template>

<style scoped>
.courbe { width: 100%; height: 320px; }
</style>
