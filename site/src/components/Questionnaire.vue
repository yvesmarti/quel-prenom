<script setup>
import { ref, reactive, computed } from 'vue'
import { normaliser } from '../lib/normalize.js'

// Mini-questionnaire : six questions, toutes facultatives. Il ne fait que remplir les préférences
// (voir lib/suggestions.js) ; chaque question peut être passée.
const props = defineProps({
  prefs: { type: Object, required: true },
  profils: { type: Array, required: true },
})
const emit = defineEmits(['termine', 'passer'])

const p = reactive(JSON.parse(JSON.stringify(props.prefs)))
const etape = ref(0)
const NB_ETAPES = 6

const SEXES = { tous: 'Peu importe', F: 'Une fille', M: 'Un garçon', X: 'Un prénom mixte' }
const POPULARITES = {
  tous: ['Peu importe', ''],
  courant: ['Très courant', 'Un prénom que l’on croise souvent'],
  connu: ['Connu sans être partout', 'On le reconnaît, sans en croiser dix par classe'],
  rare: ['Rare et original', 'Peu de bébés le reçoivent chaque année'],
}
const STYLES = {
  tous: ['Peu importe', ''],
  intemporel: ['Intemporel', 'Donné depuis longtemps et toujours présent'],
  vintage: ['Vintage', 'Un prénom d’avant, qui revient ou qui ne se donne plus guère'],
  moderne: ['Moderne', 'Un prénom récent, apparu ou monté ces dernières décennies'],
}
const LONGUEURS = {
  tous: ['Peu importe', ''],
  court: ['Court', '4 lettres ou moins'],
  moyen: ['Moyen', '5 ou 6 lettres'],
  long: ['Long', '7 lettres ou plus'],
}
const ORIGINES = ['latin', 'grec', 'hébraïque', 'arabe', 'germanique', 'celtique', 'romane', 'anglais', 'slave']

const lettresDe = (texte) => [...new Set(normaliser(texte).replace(/[^a-z]/g, ''))]
const evitees = ref(p.initialesEvitees.join(' ').toUpperCase())
const voulues = ref(p.initialesVoulues.join(' ').toUpperCase())

function basculer(liste, valeur) {
  const i = liste.indexOf(valeur)
  if (i >= 0) liste.splice(i, 1)
  else liste.push(valeur)
}

// --- Prénoms cités (à exclure / déjà aimés) ---
const saisieExclus = ref('')
const saisieAimes = ref('')
const message = ref('')
const parNorm = computed(() => {
  const m = new Map()
  for (const pr of props.profils) m.set(normaliser(pr.id), [...(m.get(normaliser(pr.id)) || []), pr])
  return m
})
const nom = (id) => props.profils.find((x) => x.id === id)?.affichage ?? id
function proposes(saisie) {
  const t = normaliser(saisie.trim())
  if (t.length < 2) return []
  return props.profils.filter((x) => normaliser(x.id).startsWith(t)).slice(0, 8)
}
function ajouter(saisie, liste) {
  const t = saisie.value.trim()
  if (!t) return
  const trouves = parNorm.value.get(normaliser(t)) || []
  const choisi = trouves.find((x) => x.id === t.toLowerCase()) || trouves[0]
  if (!choisi) {
    message.value = `« ${t} » n’est pas dans les prénoms proposés par ce site (trop rare ou jamais donné récemment).`
    return
  }
  message.value = ''
  if (!liste.includes(choisi.id)) liste.push(choisi.id)
  saisie.value = ''
}

function terminer() {
  p.initialesEvitees = lettresDe(evitees.value)
  p.initialesVoulues = lettresDe(voulues.value)
  emit('termine', JSON.parse(JSON.stringify(p)))
}
const suivant = () => (etape.value === NB_ETAPES - 1 ? terminer() : etape.value++)
</script>

<template>
  <section class="carte questionnaire" aria-labelledby="titre-quest">
    <p class="doux petit etape" aria-live="polite">Question {{ etape + 1 }} sur {{ NB_ETAPES }} · toutes sont facultatives</p>

    <!-- 1. Sexe -->
    <fieldset v-if="etape === 0">
      <legend id="titre-quest">Vous attendez…</legend>
      <div class="choix">
        <label v-for="(lib, val) in SEXES" :key="val">
          <input v-model="p.sexe" type="radio" name="sexe" :value="val" /><span>{{ lib }}</span>
        </label>
      </div>
      <p class="doux petit">« Peu importe » propose des prénoms de tous les usages. « Un prénom mixte » ne garde que ceux
        donnés aux deux sexes (Camille, Alix…).</p>
    </fieldset>

    <!-- 2. Popularité -->
    <fieldset v-else-if="etape === 1">
      <legend id="titre-quest">À quel point voulez-vous qu’il soit courant ?</legend>
      <div class="choix gros">
        <label v-for="(v, val) in POPULARITES" :key="val">
          <input v-model="p.popularite" type="radio" name="popularite" :value="val" />
          <span><strong>{{ v[0] }}</strong><small v-if="v[1]">{{ v[1] }}</small></span>
        </label>
      </div>
    </fieldset>

    <!-- 3. Style -->
    <fieldset v-else-if="etape === 2">
      <legend id="titre-quest">Plutôt quel style ?</legend>
      <div class="choix gros">
        <label v-for="(v, val) in STYLES" :key="val">
          <input v-model="p.style" type="radio" name="style" :value="val" />
          <span><strong>{{ v[0] }}</strong><small v-if="v[1]">{{ v[1] }}</small></span>
        </label>
      </div>
    </fieldset>

    <!-- 4. Sonorité -->
    <div v-else-if="etape === 3">
      <fieldset>
        <legend id="titre-quest">Longueur du prénom</legend>
        <div class="choix gros">
          <label v-for="(v, val) in LONGUEURS" :key="val">
            <input v-model="p.longueur" type="radio" name="longueur" :value="val" />
            <span><strong>{{ v[0] }}</strong><small v-if="v[1]">{{ v[1] }}</small></span>
          </label>
        </div>
      </fieldset>
      <label class="case">
        <input type="checkbox" :checked="p.compose === 'non'" @change="p.compose = $event.target.checked ? 'non' : 'tous'" />
        Sans prénoms composés (Marie-Claire…)
      </label>
      <div class="deux">
        <label class="champ"><span>Initiales à éviter</span>
          <input v-model="evitees" placeholder="ex. A M" autocomplete="off" maxlength="30" /></label>
        <label class="champ"><span>Initiales souhaitées</span>
          <input v-model="voulues" placeholder="ex. L E" autocomplete="off" maxlength="30" /></label>
      </div>
      <p class="doux petit">Pour éviter l’initiale d’un frère ou d’une sœur, ou celle de votre nom de famille.</p>
    </div>

    <!-- 5. Origines -->
    <fieldset v-else-if="etape === 4">
      <legend id="titre-quest">Des origines qui vous parlent ?</legend>
      <div class="choix">
        <label v-for="o in ORIGINES" :key="o">
          <input type="checkbox" :checked="p.origines.includes(o)" @change="basculer(p.origines, o)" />
          <span>{{ o[0].toUpperCase() + o.slice(1) }}</span>
        </label>
      </div>
      <p class="doux petit">Honnêteté : l’origine n’est connue que pour une partie des prénoms (Wiktionnaire). Ceux dont
        l’origine est inconnue ne sont pas écartés, simplement moins mis en avant.</p>
    </fieldset>

    <!-- 6. Prénoms cités -->
    <div v-else>
      <h2 id="titre-quest" class="titre-quest">Des prénoms à connaître ?</h2>
      <div class="nommer">
        <form @submit.prevent="ajouter(saisieExclus, p.exclus)">
          <label class="champ"><span>À ne jamais proposer</span>
            <input v-model="saisieExclus" list="liste-exclus" placeholder="ex. le prénom d’un proche" autocomplete="off" /></label>
          <datalist id="liste-exclus"><option v-for="x in proposes(saisieExclus)" :key="x.id" :value="x.affichage" /></datalist>
          <button class="bouton petit" type="submit">Ajouter</button>
        </form>
        <ul class="puces" aria-label="Prénoms exclus">
          <li v-for="id in p.exclus" :key="id">
            <button type="button" class="bouton petit" :aria-label="`Retirer ${nom(id)}`" @click="basculer(p.exclus, id)">{{ nom(id) }} ✕</button>
          </li>
        </ul>
        <form @submit.prevent="ajouter(saisieAimes, p.aimes)">
          <label class="champ"><span>Des prénoms que vous aimez déjà</span>
            <input v-model="saisieAimes" list="liste-aimes" placeholder="ex. Jade" autocomplete="off" /></label>
          <datalist id="liste-aimes"><option v-for="x in proposes(saisieAimes)" :key="x.id" :value="x.affichage" /></datalist>
          <button class="bouton petit" type="submit">Ajouter</button>
        </form>
        <ul class="puces" aria-label="Prénoms aimés">
          <li v-for="id in p.aimes" :key="id">
            <button type="button" class="bouton petit" :aria-label="`Retirer ${nom(id)}`" @click="basculer(p.aimes, id)">{{ nom(id) }} ✕</button>
          </li>
        </ul>
        <p v-if="message" class="doux petit" role="status">{{ message }}</p>
      </div>
      <p class="doux petit">Les prénoms aimés servent de points de départ : le site proposera des prénoms qui leur ressemblent.</p>
    </div>

    <div class="actions">
      <button v-if="etape > 0" class="bouton" type="button" @click="etape--">Précédent</button>
      <button class="bouton principal" type="button" @click="suivant">
        {{ etape === NB_ETAPES - 1 ? 'Voir les suggestions' : 'Suivant' }}
      </button>
      <button class="lien" type="button" @click="emit('passer')">Passer, surprenez-moi</button>
    </div>
  </section>
</template>

<style scoped>
.questionnaire { display: grid; gap: 16px; max-width: 640px; margin: 0 auto; }
.etape { margin: 0; }
fieldset { border: 0; padding: 0; margin: 0 0 8px; min-width: 0; }
legend, .titre-quest { font-family: var(--serif); font-size: 1.5rem; font-weight: 600; padding: 0; margin: 0 0 12px; }
.choix { display: flex; flex-wrap: wrap; gap: 8px; }
.choix label { position: relative; }
.choix input { position: absolute; opacity: 0; inset: 0; cursor: pointer; width: 100%; height: 100%; margin: 0; }
.choix span {
  display: block; padding: 8px 16px; border: 1px solid var(--bordure); border-radius: 999px; background: var(--fond);
}
.choix.gros { display: grid; gap: 8px; }
.choix.gros span { border-radius: 12px; padding: 10px 16px; display: grid; }
.choix.gros small { color: var(--texte-doux); font-size: 0.85rem; }
.choix input:checked + span { background: var(--accent-fond); border-color: var(--accent); color: var(--accent); }
.choix input:checked + span small { color: inherit; }
.choix input:focus-visible + span { outline: 3px solid var(--focus); outline-offset: 2px; }
.case { display: flex; gap: 8px; align-items: center; margin: 8px 0 12px; }
.deux { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.champ { display: grid; gap: 4px; min-width: 0; }
.champ span { font-size: 0.85rem; font-weight: 600; color: var(--texte-doux); }
.champ input { width: 100%; padding: 9px 12px; border: 1px solid var(--bordure); border-radius: 10px; background: var(--fond); }
.nommer { display: grid; gap: 10px; }
.nommer form { display: flex; gap: 8px; align-items: end; }
.nommer form .champ { flex: 1; }
.puces { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: 6px; }
.actions { display: flex; flex-wrap: wrap; gap: 8px 12px; align-items: center; }
.principal { background: var(--accent); border-color: var(--accent); color: #fff; font-weight: 600; }
.principal:hover { background: #8a3d1b; }
.lien { background: none; border: 0; color: var(--accent); text-decoration: underline; cursor: pointer; padding: 8px; margin-left: auto; }
</style>
