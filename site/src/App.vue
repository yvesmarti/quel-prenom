<script setup>
import { ref, onMounted } from 'vue'
import { chargerMeta } from './lib/dataLoader.js'
import { selection } from './lib/etatSelection.js'

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
      <nav aria-label="Navigation principale">
        <RouterLink to="/" class="nav" exact-active-class="actif">Trouver</RouterLink>
        <RouterLink to="/liste" class="nav" active-class="actif">Ma liste<template v-if="selection.gardes.length"> ({{ selection.gardes.length }})</template></RouterLink>
        <RouterLink to="/recherche" class="nav" active-class="actif">Rechercher</RouterLink>
        <RouterLink to="/classements" class="nav" active-class="actif">Classements</RouterLink>
        <RouterLink to="/tendances" class="nav" active-class="actif">Tendances</RouterLink>
        <RouterLink to="/methode" class="nav" active-class="actif">Méthode</RouterLink>
      </nav>
    </div>
  </header>

  <main ref="contenu" tabindex="-1" class="conteneur">
    <RouterView />
  </main>

  <footer class="conteneur pied doux petit">
    <p>
      Source : Insee, Fichier des prénoms – Édition {{ meta?.source.millesime ?? 2025 }}
      (<a href="https://www.insee.fr/fr/statistiques/8595130">insee.fr</a>) et statistiques de l'état civil ;
      contours IGN. Licence Ouverte 2.0 (Etalab)<template v-if="meta">, données récupérées le
      {{ new Date(meta.source.date_recuperation).toLocaleDateString('fr-FR') }}</template>.
      Informations encyclopédiques : Wikidata (CC0) et Wiktionnaire (textes sous
      <a href="https://creativecommons.org/licenses/by-sa/4.0/deed.fr">CC BY-SA 4.0</a>). Code sous licence EUPL 1.2.
      Effectifs arrondis par l'Insee au multiple de 5 ; rangs officiels Insee.
      <RouterLink to="/methode">Méthode et sources</RouterLink>
    </p>
  </footer>
</template>

<style scoped>
.lien-evitement { position: absolute; left: -999px; border: 1px solid var(--bordure); border-radius: 8px; }
main:focus { outline: none; }
.lien-evitement:focus { left: 16px; top: 8px; background: var(--surface); padding: 6px 12px; z-index: 10; }
.entete { border-bottom: 1px solid var(--bordure); background: var(--fond); }
.entete-interieur { display: flex; align-items: center; justify-content: space-between; gap: 8px 18px; flex-wrap: wrap; padding-top: 14px; padding-bottom: 12px; }
.logo { font-family: var(--serif); font-size: 1.6rem; font-weight: 700; color: var(--accent); text-decoration: none; }
nav { display: flex; flex-wrap: wrap; gap: 2px; }
.nav { padding: 6px 12px; border-radius: 999px; color: var(--texte); text-decoration: none; }
.nav:hover { background: var(--surface-douce); }
.nav.actif { background: var(--accent-fond); color: var(--accent); font-weight: 600; }
main { padding-top: 24px; padding-bottom: 40px; min-height: 60vh; }
.pied { border-top: 1px solid var(--bordure); padding-top: 8px; padding-bottom: 24px; }
</style>
