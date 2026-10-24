import { createApp } from 'vue'
import { createRouter, createWebHashHistory } from 'vue-router'
import App from './App.vue'
import Trouver from './views/Trouver.vue'
import './style.css'

// Les autres pages (et la bibliothèque de graphiques) ne sont téléchargées qu'à leur première ouverture.
const Recherche = () => import('./views/Recherche.vue')
const Liste = () => import('./views/Liste.vue')
const Fiche = () => import('./views/Fiche.vue')
const Classements = () => import('./views/Classements.vue')
const Tendances = () => import('./views/Tendances.vue')
const Methode = () => import('./views/Methode.vue')

// Mode « hash » (#/prenom/lea) : fonctionne sur un hébergement statique sans configuration.
const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', name: 'trouver', component: Trouver },
    { path: '/liste', name: 'liste', component: Liste },
    { path: '/recherche', name: 'recherche', component: Recherche },
    { path: '/prenom/:id', name: 'fiche', component: Fiche, props: true },
    { path: '/classements', name: 'classements', component: Classements },
    { path: '/tendances', name: 'tendances', component: Tendances },
    { path: '/methode', name: 'methode', component: Methode },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
  scrollBehavior: (to, from, saved) => saved || (to.hash ? { el: to.hash } : to.path === from.path ? false : { top: 0 }),
})

// La fiche remplace ce titre par le nom du prénom une fois chargée.
const TITRES = { liste: 'Ma liste', recherche: 'Rechercher', classements: 'Classements', tendances: 'Tendances', methode: 'Méthode et sources' }
router.afterEach((to) => { document.title = TITRES[to.name] ? `${TITRES[to.name]} — Prénoscope` : 'Prénoscope' })

createApp(App).use(router).mount('#app')
