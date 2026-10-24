import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  // Chemins relatifs : le site fonctionne aussi dans un sous-dossier (GitHub Pages).
  base: './',
  test: {
    environment: 'node',
  },
})
