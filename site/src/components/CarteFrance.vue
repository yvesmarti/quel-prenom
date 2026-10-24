<script setup>
// Carte choroplèthe des régions ou départements (ECharts + GeoJSON IGN simplifié).
// Les zones sans valeur (effectif insuffisant ou nul) restent en gris neutre.
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts/core'
import { MapChart } from 'echarts/charts'
import { TooltipComponent, VisualMapComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([MapChart, TooltipComponent, VisualMapComponent, CanvasRenderer])

const props = defineProps({
  niveau: { type: String, required: true }, // REG | DEP
  fond: { type: Object, required: true }, // GeoJSON
  zones: { type: Array, required: true }, // [{ code, valeur, indice }]
  noms: { type: Object, required: true }, // { code: nom }
  mesure: { type: String, default: 'indice' }, // indice | valeur
})
const emit = defineEmits(['choisir'])

// Indice : palette divergente brun / bleu-vert (lisible par les daltoniens), 100 = moyenne.
const PALIERS_INDICE = [
  { lt: 50, label: 'moins de 50', color: '#2c6e7a' },
  { gte: 50, lt: 80, label: '50 à 80', color: '#8dbcc3' },
  { gte: 80, lt: 125, label: '80 à 125', color: '#f7f1e6' },
  { gte: 125, lt: 200, label: '125 à 200', color: '#dca06a' },
  { gte: 200, label: '200 et plus', color: '#9a4a1f' },
]

const conteneur = ref(null)
let graphique = null

function options() {
  const nomCarte = `fr-${props.niveau}`
  if (!echarts.getMap(nomCarte)) echarts.registerMap(nomCarte, props.fond)
  const indice = props.mesure === 'indice'
  const donnees = props.zones.map((z) => ({ name: z.code, value: indice ? z.indice : (z.valeur || null), zone: z }))
  const max = Math.max(1, ...props.zones.map((z) => z.valeur))
  return {
    tooltip: {
      trigger: 'item',
      formatter: (p) => {
        const z = p.data?.zone
        const nom = props.noms[p.name] ?? p.name
        if (!z) return nom
        const lignes = [`<strong>${nom}</strong>`, `Naissances : ${z.valeur ? 'environ ' + z.valeur.toLocaleString('fr-FR') : 'aucune publiée'}`]
        lignes.push(z.indice != null ? `Indice : ${Math.round(z.indice)} (100 = moyenne)` : 'Indice : effectif trop faible')
        return lignes.join('<br>')
      },
    },
    visualMap: indice
      ? { type: 'piecewise', pieces: PALIERS_INDICE, left: 0, bottom: 0, itemWidth: 14, itemHeight: 10,
          textStyle: { color: '#2b2620', fontSize: 11 } }
      : { type: 'continuous', min: 0, max, left: 0, bottom: 0, calculable: false, itemHeight: 90,
          inRange: { color: ['#f6e9dc', '#dca06a', '#9a4a1f', '#4f220c'] }, text: ['plus', 'moins'],
          textStyle: { color: '#2b2620', fontSize: 11 } },
    series: [{
      type: 'map',
      map: nomCarte,
      nameProperty: 'code',
      roam: false,
      aspectScale: 0.72,
      layoutCenter: ['54%', '50%'],
      layoutSize: '100%',
      data: donnees,
      itemStyle: { areaColor: '#bfb9b0', borderColor: '#ffffff', borderWidth: props.niveau === 'DEP' ? 0.5 : 1 },
      emphasis: { label: { show: false }, itemStyle: { areaColor: '#f3c26b' } },
      select: { disabled: true },
    }],
  }
}

function redimensionner() { graphique?.resize() }

onMounted(() => {
  graphique = echarts.init(conteneur.value)
  graphique.setOption(options())
  graphique.on('click', (p) => emit('choisir', p.name))
  window.addEventListener('resize', redimensionner)
})
watch(() => [props.zones, props.mesure, props.niveau, props.fond], () => graphique?.setOption(options(), true))
onBeforeUnmount(() => {
  window.removeEventListener('resize', redimensionner)
  graphique?.dispose()
})
</script>

<template>
  <div ref="conteneur" class="carte-france" role="img"
       :aria-label="`Carte par ${niveau === 'REG' ? 'région' : 'département'} ; le tableau qui suit donne les mêmes valeurs.`"></div>
</template>

<style scoped>
.carte-france { width: 100%; height: 460px; }
@media (max-width: 600px) { .carte-france { height: 360px; } }
</style>
