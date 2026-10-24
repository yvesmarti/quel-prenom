import { createApp } from 'vue'
import { createRouter, createWebHashHistory } from 'vue-router'
import App from './App.vue'
import Recherche from './views/Recherche.vue'
import Fiche from './views/Fiche.vue'
import './style.css'

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

createApp(App).use(router).mount('#app')
