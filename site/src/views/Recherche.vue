<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { chargerIndex } from '../lib/dataLoader.js'
import { filtrer, CRITERES_VIDES } from '../lib/filters.js'
import { environ } from '../lib/normalize.js'
import { etatRecherche } from '../lib/etatRecherche.js'

const PAR_PAGE = 60
const LIBELLES_SEXE = { F: 'Féminin', M: 'Masculin', X: 'Mixte' }

const prenoms = ref([])
const chargement = ref(true)
const erreur = ref('')
const criteres = etatRecherche.criteres
const affiches = ref(etatRecherche.affiches)

async function charger() {
  chargement.value = true
  erreur.value = ''
  try {
    prenoms.value = await chargerIndex()
  } catch (e) {
    erreur.value = "Impossible de charger la liste des prénoms. Vérifiez votre connexion puis réessayez."
  } finally {
    chargement.value = false
  }
}
onMounted(charger)

const resultats = computed(() => filtrer(prenoms.value, criteres))
const ilYADesFichesCompletes = computed(() => prenoms.value.some((p) => p.qualite === 'c'))
const visibles = computed(() => resultats.value.slice(0, affiches.value))

watch(criteres, () => { affiches.value = PAR_PAGE })
watch(affiches, (n) => { etatRecherche.affiches = n })

function reinitialiser() {
  Object.assign(criteres, CRITERES_VIDES)
}
</script>

<template>
  <section aria-labelledby="titre-recherche">
    <h1 id="titre-recherche" class="titre">Rechercher un prénom</h1>
    <p class="doux intro">
      Explorez les prénoms attribués en France depuis 1900, d'après l'Insee.
    </p>

    <div class="carte filtres">
      <label class="champ champ-texte">
        <span>Rechercher</span>
        <input v-model="criteres.texte" type="search" placeholder="ex. lea, marie, ael…"
               autocomplete="off" spellcheck="false" />
        <small class="doux">Insensible aux accents et aux majuscules.</small>
      </label>

      <fieldset class="champ">
        <legend>Usage</legend>
        <div class="segments">
          <label v-for="(lib, val) in { tous: 'Tous', F: 'Féminin', M: 'Masculin', X: 'Mixte' }" :key="val">
            <input v-model="criteres.sexe" type="radio" name="sexe" :value="val" />
            <span>{{ lib }}</span>
          </label>
        </div>
      </fieldset>

      <div class="grille">
        <label class="champ">
          <span>Lettres, min.</span>
          <input v-model.number="criteres.lettresMin" type="number" min="1" max="20" inputmode="numeric" />
        </label>
        <label class="champ">
          <span>Lettres, max.</span>
          <input v-model.number="criteres.lettresMax" type="number" min="1" max="20" inputmode="numeric" />
        </label>
        <label class="champ">
          <span>Initiale</span>
          <input v-model="criteres.initiale" maxlength="1" autocomplete="off" />
        </label>
        <label class="champ">
          <span>Se termine par</span>
          <input v-model="criteres.terminaison" maxlength="10" autocomplete="off" placeholder="ex. ine" />
        </label>
        <label class="champ">
          <span>Accents</span>
          <select v-model="criteres.accent">
            <option value="tous">Indifférent</option>
            <option value="avec">Avec accent</option>
            <option value="sans">Sans accent</option>
          </select>
        </label>
        <label class="champ">
          <span>Composé (tiret)</span>
          <select v-model="criteres.compose">
            <option value="tous">Indifférent</option>
            <option value="oui">Composé</option>
            <option value="non">Simple</option>
          </select>
        </label>
        <label class="champ">
          <span>Fiche</span>
          <select v-model="criteres.fiche">
            <option value="tous">Toutes</option>
            <option value="enrichies">Avec informations encyclopédiques</option>
            <option v-if="ilYADesFichesCompletes" value="completes">Complètes uniquement</option>
          </select>
        </label>
        <label class="champ">
          <span>Tri</span>
          <select v-model="criteres.tri">
            <option value="popularite">Plus donnés depuis 1900</option>
            <option value="alpha">Ordre alphabétique</option>
          </select>
        </label>
      </div>
      <button class="bouton petit" type="button" @click="reinitialiser">Effacer les filtres</button>
    </div>

    <div v-if="chargement" class="etat" role="status">Chargement de la liste des prénoms…</div>
    <div v-else-if="erreur" class="etat erreur" role="alert">
      {{ erreur }} <button class="bouton" @click="charger">Réessayer</button>
    </div>
    <template v-else>
      <p class="compteur" role="status" aria-live="polite">
        <strong>{{ resultats.length.toLocaleString('fr-FR') }}</strong>
        prénom{{ resultats.length > 1 ? 's' : '' }} sur {{ prenoms.length.toLocaleString('fr-FR') }}
      </p>
      <p v-if="!resultats.length" class="etat doux">
        Aucun prénom ne correspond. Essayez d'élargir le nombre de lettres ou de retirer un filtre.
      </p>
      <ul class="liste">
        <li v-for="p in visibles" :key="p.id">
          <RouterLink :to="{ name: 'fiche', params: { id: p.id } }" class="ligne">
            <span class="nom">{{ p.affichage }}</span>
            <span :class="['badge', p.sexe]">{{ LIBELLES_SEXE[p.sexe] }}</span>
            <span v-if="p.qualite !== 'm'" class="doux petit" :title="p.qualite === 'c' ? 'Fiche complète' : 'Fiche partielle'">
              {{ p.qualite === 'c' ? '● fiche complète' : '◐ fiche partielle' }}</span>
            <span class="doux petit infos">
              {{ environ(p.total) }} naissances ·
              {{ p.premiereAnnee === p.derniereAnnee ? p.premiereAnnee : `${p.premiereAnnee}–${p.derniereAnnee}` }}
            </span>
          </RouterLink>
        </li>
      </ul>
      <div v-if="visibles.length < resultats.length" class="suite">
        <button class="bouton" @click="affiches += PAR_PAGE">
          Afficher {{ Math.min(PAR_PAGE, resultats.length - visibles.length) }} de plus
        </button>
      </div>
    </template>
  </section>
</template>

<style scoped>
.titre { font-size: 2rem; margin: 0 0 4px; }
.intro { margin: 0 0 20px; }
.filtres { display: grid; gap: 16px; margin-bottom: 20px; }
.champ { display: grid; gap: 4px; border: 0; margin: 0; padding: 0; min-width: 0; }
.champ > span, legend { font-size: 0.85rem; font-weight: 600; color: var(--texte-doux); padding: 0; }
.champ input, .champ select {
  width: 100%; padding: 9px 12px; border: 1px solid var(--bordure); border-radius: 10px; background: var(--fond);
}
.champ-texte input { font-size: 1.15rem; padding: 12px 14px; background: var(--surface); }
.grille { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
@media (min-width: 640px) { .grille { grid-template-columns: repeat(4, 1fr); } }
.segments { display: flex; flex-wrap: wrap; gap: 6px; }
.segments label { position: relative; }
.segments input { position: absolute; opacity: 0; inset: 0; cursor: pointer; }
.segments span {
  display: inline-block; padding: 6px 14px; border: 1px solid var(--bordure); border-radius: 999px; background: var(--fond);
}
.segments input:checked + span { background: var(--accent-fond); border-color: var(--accent); color: var(--accent); font-weight: 600; }
.segments input:focus-visible + span { outline: 3px solid var(--focus); outline-offset: 2px; }
.filtres > .bouton { justify-self: start; }
.compteur { margin: 0 0 10px; }
.etat { padding: 24px 0; }
.erreur { color: #8a1f11; }
.liste { list-style: none; margin: 0; padding: 0; display: grid; gap: 8px; }
.ligne {
  display: flex; flex-wrap: wrap; align-items: baseline; gap: 4px 12px;
  padding: 12px 16px; background: var(--surface); border: 1px solid var(--bordure); border-radius: 12px;
  color: inherit; text-decoration: none; transition: border-color 0.15s, transform 0.15s;
}
.ligne:hover { border-color: var(--accent); transform: translateY(-1px); }
.nom { font-family: var(--serif); font-size: 1.2rem; font-weight: 600; }
.infos { flex-basis: 100%; }
@media (min-width: 640px) { .infos { flex-basis: auto; margin-left: auto; } }
.suite { text-align: center; margin-top: 18px; }
</style>
