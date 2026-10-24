<script setup>
// Section « Géographie » d'une fiche : carte, zones de prédilection et tableau des valeurs.
// Rappel : il s'agit du lieu de naissance (géographie actuelle), pas d'une origine culturelle.
import { ref, computed, watch } from 'vue'
import CarteFrance from './CarteFrance.vue'
import { chargerGeoPrenom, chargerTotauxGeo, chargerFondDeCarte, chargerZones } from '../lib/dataLoader.js'
import { valeursParZone, predilection, periodes } from '../lib/geo.js'

const props = defineProps({
  prenom: { type: Object, required: true },
  meta: { type: Object, required: true },
})

const etat = ref('chargement')
const geo = ref({})
const totaux = ref(null)
const fonds = ref({})
const noms = ref({ REG: {}, DEP: {} })

const sexesDisponibles = computed(() => ['F', 'M'].filter((s) => geo.value[s]))
const sexe = ref(props.prenom.sexe === 'M' ? 'M' : 'F')
const niveau = ref('REG')
const periode = ref('tout')
const mesure = ref('indice')

const listePeriodes = computed(() => periodes(props.meta.annee_min, props.meta.annee_max))
const libellePeriode = (d) => (d === 'tout' ? `${props.meta.annee_min}–${props.meta.annee_max}`
  : d + 9 > props.meta.annee_max ? `${d}–${props.meta.annee_max}` : `années ${d}`)

async function charger() {
  etat.value = 'chargement'
  try {
    const [g, t, reg, dep, z] = await Promise.all([chargerGeoPrenom(props.prenom), chargerTotauxGeo(),
      chargerFondDeCarte('REG'), chargerFondDeCarte('DEP'), chargerZones()])
    geo.value = g
    totaux.value = t.totaux
    fonds.value = { REG: reg, DEP: dep }
    noms.value = z
    if (!g[sexe.value]) sexe.value = sexesDisponibles.value[0] ?? sexe.value
    etat.value = sexesDisponibles.value.length ? 'ok' : 'vide'
  } catch {
    etat.value = 'erreur'
  }
}
watch(() => props.prenom.id, charger, { immediate: true })

const zones = computed(() => (etat.value === 'ok'
  ? valeursParZone(geo.value[sexe.value]?.[niveau.value], totaux.value[niveau.value], sexe.value, periode.value,
    props.meta.regles.geo_min_indice)
  : []))
const preferees = computed(() => predilection(zones.value, 5))
const totalPeriode = computed(() => zones.value.reduce((s, z) => s + z.valeur, 0))
const tableau = computed(() => [...zones.value].sort((a, b) => b.valeur - a.valeur || a.code.localeCompare(b.code)))
const nomZone = (code) => noms.value[niveau.value][code] ?? code
</script>

<template>
  <section class="carte" aria-labelledby="titre-geo">
    <h2 id="titre-geo">Où naissent les {{ prenom.affichage }} ?</h2>
    <p class="doux petit">
      Lieu de naissance de l'enfant (découpage actuel des régions et départements), et non origine culturelle du prénom.
    </p>

    <div v-if="etat === 'chargement'" role="status" class="etat">Chargement des données géographiques…</div>
    <div v-else-if="etat === 'erreur'" role="alert" class="etat">
      Les données géographiques n'ont pas pu être chargées. <button class="bouton" @click="charger">Réessayer</button>
    </div>
    <p v-else-if="etat === 'vide'" class="etat doux">
      Ce prénom n'apparaît dans aucune région ni aucun département du fichier de l'Insee : ses effectifs locaux
      sont trop faibles pour être publiés.
    </p>

    <template v-else>
      <div class="controles">
        <label v-if="sexesDisponibles.length > 1">
          <span>Sexe</span>
          <select v-model="sexe"><option value="F">Filles</option><option value="M">Garçons</option></select>
        </label>
        <label>
          <span>Découpage</span>
          <select v-model="niveau"><option value="REG">Régions</option><option value="DEP">Départements</option></select>
        </label>
        <label>
          <span>Période</span>
          <select v-model="periode">
            <option value="tout">Toute la période ({{ libellePeriode('tout') }})</option>
            <option v-for="d in listePeriodes" :key="d" :value="d">{{ libellePeriode(d) }}</option>
          </select>
        </label>
        <label>
          <span>Mesure</span>
          <select v-model="mesure">
            <option value="indice">Popularité relative (indice)</option>
            <option value="valeur">Nombre de naissances</option>
          </select>
        </label>
      </div>

      <p v-if="!totalPeriode" class="etat doux">Aucune naissance publiée à ce niveau pour cette période.</p>
      <template v-else>
        <CarteFrance :niveau="niveau" :fond="fonds[niveau]" :zones="zones" :noms="noms[niveau]" :mesure="mesure" />
        <p class="doux petit note">
          <template v-if="mesure === 'indice'">
            Indice 100 : le prénom représente la même part des naissances publiées que dans l'ensemble des
            {{ niveau === 'REG' ? 'régions' : 'départements' }} ; 200 : deux fois plus. Non calculé en dessous de
            {{ meta.regles.geo_min_indice }} naissances (<span class="pastille" aria-hidden="true"></span> zones grises).
          </template>
          <template v-else>Effectifs arrondis additionnés sur la période : ordres de grandeur
            (<span class="pastille" aria-hidden="true"></span> aucune naissance publiée).</template>
          Outre-mer en encarts à gauche (échelle non respectée). Les effectifs locaux trop faibles ne sont pas publiés
          par l'Insee : les petites zones sont sous-représentées.
        </p>

        <div v-if="preferees.length" class="preferees">
          <h3>{{ niveau === 'REG' ? 'Régions' : 'Départements' }} de prédilection</h3>
          <ol>
            <li v-for="z in preferees" :key="z.code">
              <strong>{{ nomZone(z.code) }}</strong>
              <span class="doux"> — indice {{ Math.round(z.indice) }}, environ {{ z.valeur.toLocaleString('fr-FR') }} naissances</span>
            </li>
          </ol>
        </div>

        <details class="tableau">
          <summary>Tableau des valeurs ({{ zones.length }} {{ niveau === 'REG' ? 'régions' : 'départements' }})</summary>
          <table>
            <thead><tr><th scope="col">Zone</th><th scope="col">Naissances (environ)</th><th scope="col">Indice</th></tr></thead>
            <tbody>
              <tr v-for="z in tableau" :key="z.code">
                <th scope="row">{{ nomZone(z.code) }} <span class="doux">({{ z.code }})</span></th>
                <td>{{ z.valeur ? z.valeur.toLocaleString('fr-FR') : '—' }}</td>
                <td>{{ z.indice != null ? Math.round(z.indice) : 'effectif trop faible' }}</td>
              </tr>
            </tbody>
          </table>
        </details>
      </template>
    </template>
  </section>
</template>

<style scoped>
h2 { font-size: 1.25rem; margin: 0 0 4px; }
h3 { font-size: 1.05rem; margin: 16px 0 6px; }
.etat { padding: 16px 0; }
.controles { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin: 12px 0; }
@media (min-width: 720px) { .controles { grid-template-columns: repeat(4, 1fr); } }
.controles label { display: grid; gap: 3px; min-width: 0; }
.controles span { font-size: 0.82rem; font-weight: 600; color: var(--texte-doux); }
.controles select { width: 100%; padding: 7px 10px; border: 1px solid var(--bordure); border-radius: 10px; background: var(--fond); }
.note { margin: 4px 0 0; }
.pastille { display: inline-block; width: 0.8em; height: 0.8em; background: #bfb9b0; border-radius: 2px; vertical-align: -0.05em; }
.preferees ol { margin: 0; padding-left: 22px; }
.tableau { margin-top: 14px; }
.tableau summary { cursor: pointer; color: var(--accent); }
table { width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 0.92rem; }
th, td { text-align: left; padding: 5px 8px; border-bottom: 1px solid var(--bordure); }
td { font-variant-numeric: tabular-nums; }
thead th { color: var(--texte-doux); font-size: 0.82rem; }
</style>
