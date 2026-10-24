<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { chargerMeta, chargerIndexParId, chargerTendances } from '../lib/dataLoader.js'
import { ORDRE_TENDANCES, LIBELLES_TENDANCES, definitionTendance } from '../lib/tendances.js'

const route = useRoute()
const router = useRouter()
const PAR_PAGE = 50

const meta = ref(null)
const parId = ref(new Map())
const tendances = ref(null)
const etat = ref('chargement')
const categorie = ref(ORDRE_TENDANCES.includes(route.query.categorie) ? route.query.categorie : 'progression')
const sexe = ref(['F', 'M'].includes(route.query.sexe) ? route.query.sexe : 'tous')
const affiches = ref(PAR_PAGE)

async function charger() {
  etat.value = 'chargement'
  try {
    const [m, p, t] = await Promise.all([chargerMeta(), chargerIndexParId(), chargerTendances()])
    meta.value = m
    parId.value = p
    tendances.value = t
    etat.value = 'ok'
  } catch {
    etat.value = 'erreur'
  }
}
onMounted(charger)

watch([categorie, sexe], () => {
  affiches.value = PAR_PAGE
  router.replace({ query: { categorie: categorie.value, sexe: sexe.value } })
})
watch(() => route.query.categorie, (c) => { if (ORDRE_TENDANCES.includes(c)) categorie.value = c })

const liste = computed(() => (tendances.value?.categories[categorie.value] ?? [])
  .filter(([, s]) => sexe.value === 'tous' || s === sexe.value))
const compte = (cat) => tendances.value?.categories[cat]?.length ?? 0

const pct = (r) => `${r >= 1 ? '×' + r.toLocaleString('fr-FR', { maximumFractionDigits: 1 })
  : '÷' + (1 / r).toLocaleString('fr-FR', { maximumFractionDigits: 1 })}`
const n = (x) => Math.round(x).toLocaleString('fr-FR')

/** Résumé chiffré de la tendance pour une ligne. */
function resume(cat, d) {
  const t = meta.value.regles.tendances
  const Y = meta.value.annee_max
  const recent = `${Y - t.fenetre + 1}–${Y}`
  const ancien = `${Y - t.decalage_progression - t.fenetre + 1}–${Y - t.decalage_progression}`
  switch (cat) {
    case 'emergent': return `≈ ${n(d.effectif_recent)} naissances/an sur ${recent}`
    case 'progression':
    case 'declin': return `fréquence ${pct(d.ratio_frequence ?? 0)} — ≈ ${n(d.effectif_ancien)} puis ${n(d.effectif_recent)} naissances/an (${ancien} → ${recent})`
    case 'devenu_rare': return `apogée ≈ ${n(d.pic_moyen_5_ans)} naissances/an, aujourd'hui ≈ ${n(d.effectif_recent)}`
    case 'retour': return `sommets : ${d.sommet_ancien[0]} (rang ≈ ${d.sommet_ancien[1]}) puis ${d.sommet_recent[0]} (rang ≈ ${d.sommet_recent[1]})`
    case 'vagues': return `sommets : ${d.sommets.map((s) => `${s[0]} (rang ≈ ${s[1]})`).join(', ')}`
    default: return ''
  }
}
</script>

<template>
  <section aria-labelledby="titre-tendances">
    <h1 id="titre-tendances" class="titre">Tendances</h1>
    <p class="doux intro">
      Prénoms qui montent, qui reviennent ou qui s'effacent, selon des règles chiffrées identiques pour tous.
      Ce sont des constats sur le passé, pas des prédictions.
    </p>

    <div v-if="etat === 'chargement'" role="status" class="etat">Chargement des tendances…</div>
    <div v-else-if="etat === 'erreur'" role="alert" class="etat">
      Les tendances n'ont pas pu être chargées. <button class="bouton" @click="charger">Réessayer</button>
    </div>
    <template v-else>
      <div class="onglets" role="group" aria-label="Type de tendance">
        <button v-for="c in ORDRE_TENDANCES" :key="c" :aria-pressed="categorie === c"
                :class="{ actif: categorie === c }" @click="categorie = c">
          {{ LIBELLES_TENDANCES[c] }} <span class="compte">{{ compte(c) }}</span>
        </button>
      </div>

      <div class="carte definition">
        <p><strong>Définition.</strong> {{ definitionTendance(categorie, meta.regles.tendances, meta.annee_max) }}</p>
        <p class="doux petit">
          Fréquences calculées avec la série officielle des naissances par sexe ; rangs officiels de l'Insee.
          Une année absente du fichier compte comme « au plus 2 naissances » (effectif arrondi à 0).
          <RouterLink to="/methode">Méthode détaillée</RouterLink>
        </p>
        <label class="sexe">
          <span>Sexe</span>
          <select v-model="sexe">
            <option value="tous">Tous</option><option value="F">Filles</option><option value="M">Garçons</option>
          </select>
        </label>
      </div>

      <p class="compteur" role="status" aria-live="polite">
        {{ liste.length.toLocaleString('fr-FR') }} prénom{{ liste.length > 1 ? 's' : '' }}
      </p>
      <ol class="liste">
        <li v-for="[id, s, , d] in liste.slice(0, affiches)" :key="id + s">
          <RouterLink :to="{ name: 'fiche', params: { id } }" class="ligne">
            <span class="nom">{{ parId.get(id)?.affichage ?? id }}</span>
            <span :class="['badge', s]">{{ s === 'F' ? 'Filles' : 'Garçons' }}</span>
            <span class="doux petit infos">{{ resume(categorie, d) }}</span>
          </RouterLink>
        </li>
      </ol>
      <div v-if="affiches < liste.length" class="suite">
        <button class="bouton" @click="affiches += PAR_PAGE">Afficher plus</button>
      </div>
    </template>
  </section>
</template>

<style scoped>
.titre { font-size: 2rem; margin: 0 0 4px; }
.intro { margin: 0 0 20px; }
.etat { padding: 24px 0; }
.onglets { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px; }
.onglets button {
  border: 1px solid var(--bordure); background: var(--surface); border-radius: 999px; padding: 6px 14px; cursor: pointer;
}
.onglets button.actif { background: var(--accent-fond); border-color: var(--accent); color: var(--accent); font-weight: 600; }
.compte { font-size: 0.8rem; color: var(--texte-doux); margin-left: 2px; }
.definition p { margin: 0 0 8px; }
.sexe { display: inline-grid; gap: 4px; }
.sexe span { font-size: 0.85rem; font-weight: 600; color: var(--texte-doux); }
.sexe select { padding: 7px 12px; border: 1px solid var(--bordure); border-radius: 10px; background: var(--fond); }
.compteur { margin: 16px 0 8px; }
.liste { list-style: none; margin: 0; padding: 0; display: grid; gap: 8px; }
.ligne {
  display: flex; flex-wrap: wrap; align-items: baseline; gap: 4px 12px; padding: 12px 16px;
  background: var(--surface); border: 1px solid var(--bordure); border-radius: 12px; color: inherit; text-decoration: none;
}
.ligne:hover { border-color: var(--accent); }
.nom { font-family: var(--serif); font-size: 1.2rem; font-weight: 600; }
.infos { flex-basis: 100%; }
.suite { text-align: center; margin-top: 18px; }
</style>
