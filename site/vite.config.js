import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  // Chemins relatifs : le site fonctionne aussi dans un sous-dossier (GitHub Pages).
  base: './',
  // La fiche embarque ECharts (~175 Ko compressés), chargée seulement à l'ouverture d'une fiche.
  build: { chunkSizeWarningLimit: 600 },
  test: {
    environment: 'node',
  },
})
