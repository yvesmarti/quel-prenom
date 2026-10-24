<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { chargerMeta, chargerIndexParId, chargerZones, chargerClassementAnnee,
  chargerClassementDecennies, chargerClassementZone } from '../lib/dataLoader.js'
import { avecRangOfficiel, avecRangCalcule } from '../lib/classements.js'
import { frequence } from '../lib/indicateurs.js'
import { zonesTriees } from '../lib/geo.js'

const route = useRoute()
const router = useRouter()

const meta = ref(null)
const parId = ref(new Map())
const zonesNoms = ref({ REG: {}, DEP: {} })
const donnees = ref(null)
const etat = ref('chargement')

// Les choix sont gardés dans l'adresse : un classement peut être partagé ou mis en favori.
const q = route.query
const territoire = ref(q.territoire || 'FR') // FR | REG-xx | DEP-xx
const typePeriode = ref(q.periode === 'decennie' ? 'decennie' : 'annee')
const annee = ref(Number(q.annee) || null)
const decennie = ref(Number(q.decennie) || null)
const sexe = ref(q.sexe === 'M' ? 'M' : 'F')
const taille = ref(Number(q.taille) || 50)
const vue = ref(q.vue === 'fin' ? 'fin' : 'top')

onMounted(async () => {
  try {
    const [m, p, z] = await Promise.all([chargerMeta(), chargerIndexParId(), chargerZones()])
    meta.value = m
    parId.value = p
    zonesNoms.value = z
    annee.value ??= m.annee_max
    decennie.value ??= Math.floor(m.annee_max / 10) * 10
    await charger()
  } catch {
    etat.value = 'erreur'
  }
})

const annees = computed(() => (meta.value ? Array.from({ length: meta.value.annee_max - meta.value.annee_min + 1 },
  (_, i) => meta.value.annee_max - i) : []))
const decennies = computed(() => annees.value.filter((a) => a % 10 === 0))
const estFrance = computed(() => territoire.value === 'FR')
const niveau = computed(() => territoire.value.split('-')[0])
const code = computed(() => territoire.value.slice(4))
const tailleMax = computed(() => {
  if (estFrance.value) return typePeriode.value === 'annee' ? 500 : 100
  return meta.value?.regles.classement_territorial_top[niveau.value] ?? 20
})
const tailles = computed(() => [10, 20, 50, 100, 500].filter((t) => t <= tailleMax.value))
const officiel = computed(() => typePeriode.value === 'annee')

async function charger() {
  etat.value = 'chargement'
  try {
    if (estFrance.value) {
      donnees.value = typePeriode.value === 'annee' ? await chargerClassementAnnee(annee.value)
        : await chargerClassementDecennies()
    } else {
      donnees.value = await chargerClassementZone(niveau.value, code.value)
    }
    etat.value = 'ok'
  } catch {
    etat.value = 'erreur'
  }
}

watch([territoire, typePeriode, annee, decennie, sexe, taille, vue], () => {
  if (!tailles.value.includes(taille.value)) taille.value = tailles.value.at(-1)
  router.replace({ query: { territoire: territoire.value, periode: typePeriode.value, annee: annee.value,
    decennie: decennie.value, sexe: sexe.value, taille: taille.value, vue: vue.value } })
})
watch([territoire, typePeriode, annee], () => { if (meta.value) charger() })

const lignes = computed(() => {
  if (etat.value !== 'ok' || !donnees.value) return []
  const d = donnees.value
  let liste
  if (estFrance.value && typePeriode.value === 'annee') {
    if (vue.value === 'fin') return d[sexe.value].fin.map(([id, valeur, rang]) => ({ id, valeur, rang }))
    liste = avecRangOfficiel(d[sexe.value].top)
  } else if (estFrance.value) {
    liste = avecRangCalcule(d.decennies[decennie.value]?.[sexe.value] ?? [])
  } else if (typePeriode.value === 'annee') {
    liste = avecRangOfficiel(d.annees[annee.value]?.[sexe.value] ?? [])
  } else {
    liste = avecRangCalcule(d.decennies[decennie.value]?.[sexe.value] ?? [])
  }
  return liste.slice(0, taille.value)
})

const nomTerritoire = computed(() => (estFrance.value ? 'France'
  : zonesNoms.value[niveau.value][code.value] ?? code.value))
const nbPublies = computed(() => (estFrance.value && typePeriode.value === 'annee' ? donnees.value?.[sexe.value]?.nb_publies : null))
const affichage = (id) => parId.value.get(id)?.affichage ?? id
const freq = (v) => {
  if (!estFrance.value || typePeriode.value !== 'annee') return null
  const f = frequence(v, annee.value, sexe.value, meta.value.naissances)
  return f == null ? null : f.toLocaleString('fr-FR', { maximumFractionDigits: 2 })
}
const libelleDecennie = (d) => (d + 9 > (meta.value?.annee_max ?? 0) ? `${d}–${meta.value.annee_max}` : `Années ${d}`)
</script>

<template>
  <section aria-labelledby="titre-classements">
    <h1 id="titre-classements" class="titre">Classements</h1>
    <p class="doux intro">Les prénoms les plus donnés, par année ou par décennie, en France, par région ou par département.</p>

    <div class="carte filtres">
      <label>
        <span>Territoire</span>
        <select v-model="territoire">
          <option value="FR">France entière</option>
          <optgroup label="Régions">
            <option v-for="[c, nom] in zonesTriees(zonesNoms.REG, 'REG')" :key="c" :value="`REG-${c}`">{{ nom }}</option>
          </optgroup>
          <optgroup label="Départements">
            <option v-for="[c, nom] in zonesTriees(zonesNoms.DEP, 'DEP')" :key="c" :value="`DEP-${c}`">{{ c }} – {{ nom }}</option>
          </optgroup>
        </select>
      </label>
      <label>
        <span>Période</span>
        <select v-model="typePeriode">
          <option value="annee">Une année</option>
          <option value="decennie">Une décennie</option>
        </select>
      </label>
      <label v-if="typePeriode === 'annee'">
        <span>Année</span>
        <select v-model.number="annee"><option v-for="a in annees" :key="a" :value="a">{{ a }}</option></select>
      </label>
      <label v-else>
        <span>Décennie</span>
        <select v-model.number="decennie"><option v-for="d in decennies" :key="d" :value="d">{{ libelleDecennie(d) }}</option></select>
      </label>
      <label>
        <span>Sexe</span>
        <select v-model="sexe"><option value="F">Filles</option><option value="M">Garçons</option></select>
      </label>
      <label v-if="!(estFrance && typePeriode === 'annee' && vue === 'fin')">
        <span>Nombre</span>
        <select v-model.number="taille"><option v-for="t in tailles" :key="t" :value="t">Top {{ t }}</option></select>
      </label>
      <label v-if="estFrance && typePeriode === 'annee'">
        <span>Affichage</span>
        <select v-model="vue">
          <option value="top">Les plus donnés</option>
          <option value="fin">Fin de classement (les plus rares publiés)</option>
        </select>
      </label>
    </div>

    <p class="doux petit note">
      <template v-if="officiel">
        <strong>Rangs officiels de l'Insee</strong>, calculés sur les effectifs exacts (non arrondis).
      </template>
      <template v-else>
        <strong>Classement calculé par Prénoscope</strong> : somme des effectifs arrondis de la décennie ;
        les ex æquo partagent le même rang. Ce n'est pas un classement officiel.
      </template>
      <template v-if="!estFrance">
        Pour les régions et départements, seuls les {{ tailleMax }} premiers sont publiés ici, pour limiter la taille du site.
        Lieu de naissance, découpage territorial actuel.
      </template>
      <template v-if="vue === 'fin' && estFrance && officiel">
        Les {{ lignes.length }} derniers rangs parmi les {{ nbPublies?.toLocaleString('fr-FR') }} prénoms publiés cette année-là.
        Un effectif publié de 5 correspond à 3 à 7 naissances ; les prénoms plus rares ne sont pas publiés par l'Insee.
      </template>
    </p>

    <div v-if="etat === 'chargement'" role="status" class="etat">Chargement du classement…</div>
    <div v-else-if="etat === 'erreur'" role="alert" class="etat">
      Le classement n'a pas pu être chargé. <button class="bouton" @click="charger">Réessayer</button>
    </div>
    <template v-else>
      <h2 class="sous-titre">
        {{ sexe === 'F' ? 'Filles' : 'Garçons' }} — {{ nomTerritoire }} —
        {{ typePeriode === 'annee' ? annee : libelleDecennie(decennie) }}
      </h2>
      <p v-if="!lignes.length" class="doux">Aucun prénom publié pour cette sélection.</p>
      <table v-else class="carte tableau">
        <thead>
          <tr>
            <th scope="col">Rang</th><th scope="col">Prénom</th><th scope="col">Naissances (environ)</th>
            <th v-if="estFrance && officiel" scope="col">Pour 1 000</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="l in lignes" :key="l.id">
            <td class="rang">{{ l.rang }}</td>
            <th scope="row"><RouterLink :to="{ name: 'fiche', params: { id: l.id } }">{{ affichage(l.id) }}</RouterLink></th>
            <td>{{ l.valeur.toLocaleString('fr-FR') }}</td>
            <td v-if="estFrance && officiel">{{ freq(l.valeur) ?? '—' }}</td>
          </tr>
        </tbody>
      </table>
    </template>
  </section>
</template>

<style scoped>
.titre { font-size: 2rem; margin: 0 0 4px; }
.intro { margin: 0 0 20px; }
.filtres { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
@media (min-width: 760px) { .filtres { grid-template-columns: repeat(3, 1fr); } }
.filtres label { display: grid; gap: 4px; min-width: 0; }
.filtres span { font-size: 0.85rem; font-weight: 600; color: var(--texte-doux); }
.filtres select { width: 100%; padding: 9px 12px; border: 1px solid var(--bordure); border-radius: 10px; background: var(--fond); }
.note { margin: 12px 0; }
.sous-titre { font-size: 1.2rem; margin: 18px 0 10px; }
.etat { padding: 24px 0; }
.tableau { width: 100%; border-collapse: separate; border-spacing: 0; padding: 6px 12px; }
.tableau th, .tableau td { text-align: left; padding: 7px 8px; border-bottom: 1px solid var(--bordure); }
.tableau tbody tr:last-child > * { border-bottom: 0; }
.tableau thead th { font-size: 0.82rem; color: var(--texte-doux); }
.tableau td { font-variant-numeric: tabular-nums; }
.tableau tbody th a { font-family: var(--serif); font-size: 1.08rem; text-decoration: none; }
.rang { width: 4em; color: var(--texte-doux); }
</style>
