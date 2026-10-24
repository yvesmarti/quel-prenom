<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { chargerProfils } from '../lib/dataLoader.js'
import { suggerer, aDesPreferences, preferencesVides } from '../lib/suggestions.js'
import { selection, garder, ecarter, revoirPlusTard, annulerDernier } from '../lib/etatSelection.js'
import Questionnaire from '../components/Questionnaire.vue'
import CarteSuggestion from '../components/CarteSuggestion.vue'

const profils = ref([])
const chargement = ref(true)
const erreur = ref('')
const courant = ref(null) // { prenom, raisons }
const assouplis = ref([])
const modifier = ref(false) // questionnaire rouvert par le visiteur

const parId = computed(() => new Map(profils.value.map((p) => [p.id, p])))
const affichageQuestionnaire = computed(() => !chargement.value && !erreur.value && (modifier.value || selection.questionnaire === 'a_faire'))
const LIBELLES_ASSOUPLI = {
  longueur: 'la longueur', compose: 'les prénoms composés', initialesEvitees: 'les initiales à éviter',
  initialesVoulues: 'les initiales souhaitées',
}

async function charger() {
  chargement.value = true
  erreur.value = ''
  try {
    profils.value = await chargerProfils()
    prochain()
  } catch {
    erreur.value = 'Impossible de charger les prénoms. Vérifiez votre connexion puis réessayez.'
  } finally {
    chargement.value = false
  }
}

/** Calcule la prochaine suggestion d'après les préférences et l'historique des choix. */
function prochain() {
  const etat = {
    gardes: selection.gardes, ecartes: selection.ecartes, vus: selection.plusTard,
    recents: selection.historique.slice(-3).map((h) => h.id),
  }
  const { suggestions, assouplis: a } = suggerer(profils.value, selection.prefs, etat, 1)
  courant.value = suggestions[0] ?? null
  assouplis.value = a
}

function agir(action) {
  if (!courant.value) return
  const id = courant.value.prenom.id
  ;({ garder, ecarter, plusTard: revoirPlusTard }[action])(id)
  prochain()
}
function annuler() {
  const id = annulerDernier()
  const p = id && parId.value.get(id)
  if (p) courant.value = { prenom: p, raisons: [] }
}

function questionnaireTermine(prefs) {
  selection.prefs = prefs
  selection.questionnaire = 'fait'
  modifier.value = false
  prochain()
}
function questionnairePasse() {
  if (selection.questionnaire === 'a_faire') selection.questionnaire = 'passe'
  modifier.value = false
  prochain()
}
function recommencer() {
  selection.prefs = preferencesVides()
  modifier.value = true
}

// Raccourcis clavier : ← écarter, → garder, ↓ plus tard (hors champs de saisie).
function touche(e) {
  if (affichageQuestionnaire.value || e.altKey || e.ctrlKey || e.metaKey) return
  if (/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement?.tagName)) return
  const action = { ArrowLeft: 'ecarter', ArrowRight: 'garder', ArrowDown: 'plusTard' }[e.key]
  if (action) { e.preventDefault(); agir(action) }
}
onMounted(() => { charger(); window.addEventListener('keydown', touche) })
onBeforeUnmount(() => window.removeEventListener('keydown', touche))

const resumePrefs = computed(() => {
  const p = selection.prefs
  const t = []
  if (p.sexe !== 'tous') t.push({ F: 'fille', M: 'garçon', X: 'prénom mixte' }[p.sexe])
  if (p.popularite !== 'tous') t.push({ courant: 'très courant', connu: 'connu', rare: 'rare' }[p.popularite])
  if (p.style !== 'tous') t.push(p.style)
  if (p.longueur !== 'tous') t.push(`longueur ${p.longueur}`)
  if (p.compose === 'non') t.push('sans composés')
  if (p.initialesEvitees.length) t.push(`sans ${p.initialesEvitees.join(', ').toUpperCase()}`)
  if (p.initialesVoulues.length) t.push(`en ${p.initialesVoulues.join(', ').toUpperCase()}`)
  if (p.origines.length) t.push(`origine ${p.origines.join(' ou ')}`)
  return t
})
const nbChoix = computed(() => selection.gardes.length + selection.ecartes.length + selection.plusTard.length)
</script>

<template>
  <section aria-labelledby="titre-trouver">
    <h1 id="titre-trouver" class="titre">Trouver le prénom de votre bébé</h1>

    <div v-if="chargement" class="etat" role="status">Chargement des prénoms…</div>
    <div v-else-if="erreur" class="etat erreur" role="alert">
      {{ erreur }} <button class="bouton" @click="charger">Réessayer</button>
    </div>

    <template v-else-if="affichageQuestionnaire">
      <p class="doux intro">Quelques questions pour des suggestions sur mesure. Vous pouvez tout passer : le site vous
        proposera des prénoms variés, et s’ajustera à ce que vous gardez ou écartez.</p>
      <Questionnaire :prefs="selection.prefs" :profils="profils" @termine="questionnaireTermine" @passer="questionnairePasse" />
    </template>

    <template v-else>
      <p class="doux intro">
        <template v-if="resumePrefs.length">Vos critères : {{ resumePrefs.join(' · ') }}.</template>
        <template v-else>Aucun critère : voici des prénoms variés pour découvrir ce qui vous plaît.</template>
        <button class="lien" type="button" @click="modifier = true">Modifier les critères</button>
        <button v-if="aDesPreferences(selection.prefs)" class="lien" type="button" @click="recommencer">Tout effacer</button>
      </p>
      <p v-if="assouplis.length" class="info" role="status">
        Peu de prénoms correspondent à tous vos critères : nous avons élargi
        {{ assouplis.map((a) => LIBELLES_ASSOUPLI[a]).join(', ') }}.
      </p>

      <div v-if="courant" class="carte jeu">
        <CarteSuggestion :prenom="courant.prenom" :raisons="courant.raisons" :sexe="selection.prefs.sexe" />
        <div class="boutons" role="group" aria-label="Que pensez-vous de ce prénom ?">
          <button class="bouton ecarter" type="button" @click="agir('ecarter')">✕ Écarter</button>
          <button class="bouton tard" type="button" @click="agir('plusTard')">À revoir</button>
          <button class="bouton garder" type="button" @click="agir('garder')">♥ Garder</button>
        </div>
        <p class="doux petit aide">
          Clavier : ← écarter · ↓ à revoir · → garder.
          <button class="lien" type="button" :disabled="!selection.historique.length" @click="annuler">Annuler le dernier choix</button>
        </p>
      </div>
      <p v-else class="etat doux">
        Vous avez fait le tour des prénoms qui correspondent à vos critères. Modifiez-les pour en voir d’autres.
      </p>

      <p class="bilan" role="status">
        <RouterLink to="/liste">Ma liste</RouterLink> :
        {{ selection.gardes.length }} gardé{{ selection.gardes.length > 1 ? 's' : '' }},
        {{ selection.plusTard.length }} à revoir, {{ selection.ecartes.length }} écarté{{ selection.ecartes.length > 1 ? 's' : '' }}
        <span v-if="nbChoix" class="doux">· vos choix sont conservés sur cet appareil</span>
      </p>
    </template>
  </section>
</template>

<style scoped>
.titre { font-size: 2rem; margin: 0 0 4px; }
.intro { margin: 0 0 16px; }
.etat { padding: 24px 0; }
.erreur { color: #8a1f11; }
.info { background: var(--accent-fond); border-radius: 10px; padding: 8px 14px; margin: 0 0 14px; }
.jeu { display: grid; gap: 16px; max-width: 640px; margin: 0 auto; }
.boutons { display: grid; grid-template-columns: 1fr 1fr 1.3fr; gap: 10px; }
.boutons .bouton { padding: 14px 8px; font-size: 1.05rem; }
.ecarter { color: #8a1f11; }
.garder { background: var(--accent); border-color: var(--accent); color: #fff; font-weight: 600; }
.garder:hover { background: #8a3d1b; }
.aide { margin: 0; text-align: center; }
.lien { background: none; border: 0; color: var(--accent); text-decoration: underline; cursor: pointer; padding: 0 6px; }
.lien:disabled { color: var(--texte-doux); cursor: default; text-decoration: none; }
.bilan { max-width: 640px; margin: 16px auto 0; }
</style>
