import { createApp } from 'vue'
import { createRouter, createWebHashHistory } from 'vue-router'
import App from './App.vue'
import Recherche from './views/Recherche.vue'
import './style.css'

// La fiche (et la bibliothèque de graphiques) n'est téléchargée qu'à la première ouverture.
const Fiche = () => import('./views/Fiche.vue')

// Mode « hash » (#/prenom/lea) : fonctionne sur un hébergement statique sans configuration.
const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', name: 'recherche', component: Recherche },
    { path: '/prenom/:id', name: 'fiche', component: Fiche, props: true },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
  scrollBehavior: (to, from, saved) => saved || { top: 0 },
})

// La fiche remplace ce titre par le nom du prénom une fois chargée.
router.afterEach(() => { document.title = 'Prénoscope' })

createApp(App).use(router).mount('#app')
