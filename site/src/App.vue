<script setup>
import { ref, onMounted } from 'vue'
import { chargerMeta } from './lib/dataLoader.js'

const meta = ref(null)
const contenu = ref(null)
onMounted(async () => {
  try { meta.value = await chargerMeta() } catch { /* le pied de page reste sans date */ }
})
</script>

<template>
  <!-- Bouton plutôt qu'ancre : avec le routeur en mode « hash », #contenu changerait de page. -->
  <button class="lien-evitement" @click="contenu?.focus()">Aller au contenu</button>
  <header class="entete">
    <div class="conteneur entete-interieur">
      <RouterLink to="/" class="logo">Prénoscope</RouterLink>
      <span class="doux petit">Les prénoms donnés en France depuis 1900</span>
    </div>
  </header>

  <main ref="contenu" tabindex="-1" class="conteneur">
    <RouterView />
  </main>

  <footer class="conteneur pied doux petit">
    <p>
      Source : Insee, Fichier des prénoms – Édition {{ meta?.source.millesime ?? 2025 }}
      (<a href="https://www.insee.fr/fr/statistiques/8595130">insee.fr</a>),
      sous Licence Ouverte 2.0 (Etalab)<template v-if="meta">, données récupérées le
      {{ new Date(meta.source.date_recuperation).toLocaleDateString('fr-FR') }}</template>.
      Effectifs arrondis par l'Insee au multiple de 5 ; rangs officiels Insee.
    </p>
  </footer>
</template>

<style scoped>
.lien-evitement { position: absolute; left: -999px; border: 1px solid var(--bordure); border-radius: 8px; }
main:focus { outline: none; }
.lien-evitement:focus { left: 16px; top: 8px; background: var(--surface); padding: 6px 12px; z-index: 10; }
.entete { border-bottom: 1px solid var(--bordure); background: var(--fond); }
.entete-interieur { display: flex; align-items: baseline; gap: 14px; flex-wrap: wrap; padding-top: 18px; padding-bottom: 14px; }
.logo { font-family: var(--serif); font-size: 1.6rem; font-weight: 700; color: var(--accent); text-decoration: none; }
main { padding-top: 24px; padding-bottom: 40px; min-height: 60vh; }
.pied { border-top: 1px solid var(--bordure); padding-top: 8px; padding-bottom: 24px; }
</style>
