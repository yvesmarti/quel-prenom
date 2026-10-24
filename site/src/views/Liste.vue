<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { chargerProfils } from '../lib/dataLoader.js'
import { selection, garder, remettre, ecarter, remplacer, toutEffacer } from '../lib/etatSelection.js'
import { encoderPartage, decoderPartage, exporterJson, importerJson } from '../lib/selection.js'

const route = useRoute()
const profils = ref([])
const copie = ref('')
const messageImport = ref('')
const confirmerEffacement = ref(false)

onMounted(async () => {
  try { profils.value = await chargerProfils() } catch { /* les identifiants s'affichent tels quels */ }
})
const parId = computed(() => new Map(profils.value.map((p) => [p.id, p])))
const nom = (id) => parId.value.get(id)?.affichage ?? id.charAt(0).toUpperCase() + id.slice(1)

// Liste reçue par lien : #/liste?g=lea,jade (comparaison avec la sienne, sans rien modifier).
const recus = computed(() => decoderPartage(route.query.g))
const communs = computed(() => recus.value.filter((id) => selection.gardes.includes(id)))
const lienPartage = computed(() => {
  const base = location.href.split('#')[0]
  return `${base}#/liste?g=${encoderPartage(selection.gardes)}`
})

async function copierLien() {
  try {
    await navigator.clipboard.writeText(lienPartage.value)
    copie.value = 'Lien copié.'
  } catch {
    copie.value = 'Copie impossible : sélectionnez le lien ci-dessous.'
  }
}
function exporter() {
  const a = document.createElement('a')
  a.href = URL.createObjectURL(new Blob([exporterJson(selection)], { type: 'application/json' }))
  a.download = 'ma-liste-prenoscope.json'
  a.click()
  URL.revokeObjectURL(a.href)
}
async function importer(e) {
  const fichier = e.target.files?.[0]
  e.target.value = ''
  if (!fichier) return
  const sel = importerJson(await fichier.text())
  if (sel) {
    remplacer(sel)
    messageImport.value = 'Liste importée.'
  } else messageImport.value = 'Ce fichier n’est pas une liste Prénoscope.'
}
function ajouterRecus() {
  for (const id of recus.value) if (!selection.gardes.includes(id) && !selection.ecartes.includes(id)) garder(id)
}
function effacer() {
  toutEffacer()
  confirmerEffacement.value = false
}
</script>

<template>
  <section aria-labelledby="titre-liste">
    <h1 id="titre-liste" class="titre">Ma liste</h1>
    <p class="doux intro">Vos choix restent sur cet appareil (dans ce navigateur) : aucun compte, rien n’est envoyé.</p>

    <div v-if="recus.length" class="carte recus">
      <h2>Une liste partagée avec vous</h2>
      <p>
        <template v-if="communs.length">Vous avez {{ communs.length }} prénom{{ communs.length > 1 ? 's' : '' }} en commun :
          <strong>{{ communs.map(nom).join(', ') }}</strong>.</template>
        <template v-else>Aucun prénom en commun pour l’instant.</template>
      </p>
      <ul class="puces">
        <li v-for="id in recus" :key="id">
          <RouterLink :to="{ name: 'fiche', params: { id } }" :class="{ commun: communs.includes(id) }">{{ nom(id) }}</RouterLink>
        </li>
      </ul>
      <button class="bouton petit" type="button" @click="ajouterRecus">Ajouter ces prénoms à ma liste</button>
    </div>

    <h2>Gardés <span class="doux">({{ selection.gardes.length }})</span></h2>
    <p v-if="!selection.gardes.length" class="doux">
      Aucun prénom gardé pour l’instant. <RouterLink to="/">Découvrir des suggestions</RouterLink>
    </p>
    <ul class="lignes">
      <li v-for="id in selection.gardes" :key="id">
        <RouterLink :to="{ name: 'fiche', params: { id } }" class="nom">{{ nom(id) }}</RouterLink>
        <span class="actions">
          <button class="bouton petit" type="button" @click="ecarter(id)">Écarter</button>
          <button class="bouton petit" type="button" :aria-label="`Retirer ${nom(id)} de la liste`" @click="remettre(id)">Retirer</button>
        </span>
      </li>
    </ul>

    <template v-if="selection.plusTard.length">
      <h2>À revoir <span class="doux">({{ selection.plusTard.length }})</span></h2>
      <ul class="lignes">
        <li v-for="id in selection.plusTard" :key="id">
          <RouterLink :to="{ name: 'fiche', params: { id } }" class="nom">{{ nom(id) }}</RouterLink>
          <span class="actions">
            <button class="bouton petit" type="button" @click="garder(id)">Garder</button>
            <button class="bouton petit" type="button" @click="ecarter(id)">Écarter</button>
          </span>
        </li>
      </ul>
    </template>

    <template v-if="selection.ecartes.length">
      <h2>Écartés <span class="doux">({{ selection.ecartes.length }})</span></h2>
      <p class="doux petit">Ils ne seront plus proposés. Vous pouvez en remettre un en circulation.</p>
      <ul class="puces">
        <li v-for="id in selection.ecartes" :key="id">
          <button class="bouton petit" type="button" :aria-label="`Remettre ${nom(id)} en circulation`" @click="remettre(id)">{{ nom(id) }} ↺</button>
        </li>
      </ul>
    </template>

    <div class="carte outils">
      <h2>Partager, sauvegarder</h2>
      <div v-if="selection.gardes.length">
        <p class="petit doux">Envoyez ce lien à votre partenaire : sa page ouvrira votre liste et indiquera les prénoms que vous avez en commun.</p>
        <p><button class="bouton petit" type="button" @click="copierLien">Copier le lien de ma liste</button>
          <span class="petit" role="status">{{ copie }}</span></p>
        <input class="lien-partage" readonly :value="lienPartage" aria-label="Lien de partage" @focus="$event.target.select()" />
      </div>
      <p>
        <button class="bouton petit" type="button" @click="exporter">Enregistrer un fichier</button>
        <label class="bouton petit fichier">Importer un fichier<input type="file" accept="application/json,.json" @change="importer" /></label>
        <span class="petit" role="status">{{ messageImport }}</span>
      </p>
      <p v-if="!confirmerEffacement"><button class="bouton petit" type="button" @click="confirmerEffacement = true">Tout effacer</button></p>
      <p v-else class="petit">Effacer vos choix et vos critères sur cet appareil ?
        <button class="bouton petit" type="button" @click="effacer">Oui, tout effacer</button>
        <button class="bouton petit" type="button" @click="confirmerEffacement = false">Non</button></p>
    </div>
  </section>
</template>

<style scoped>
.titre { font-size: 2rem; margin: 0 0 4px; }
.intro { margin: 0 0 16px; }
h2 { font-size: 1.3rem; margin: 24px 0 8px; }
.recus h2, .outils h2 { margin-top: 0; }
.recus, .outils { margin: 16px 0; display: grid; gap: 8px; }
.lignes { list-style: none; margin: 0; padding: 0; display: grid; gap: 8px; }
.lignes li {
  display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 8px;
  padding: 10px 16px; background: var(--surface); border: 1px solid var(--bordure); border-radius: 12px;
}
.nom { font-family: var(--serif); font-size: 1.2rem; font-weight: 600; text-decoration: none; }
.actions { display: flex; gap: 6px; }
.puces { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: 6px 12px; }
.commun { font-weight: 700; }
.lien-partage { width: 100%; padding: 8px 12px; border: 1px solid var(--bordure); border-radius: 10px; background: var(--fond); }
.fichier { position: relative; display: inline-block; margin-left: 6px; }
.fichier input { position: absolute; inset: 0; opacity: 0; cursor: pointer; width: 100%; }
.fichier:focus-within { outline: 3px solid var(--focus); outline-offset: 2px; }
</style>
