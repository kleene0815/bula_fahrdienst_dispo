import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// In Docker zeigt VITE_API_BASE_URL auf den Backend-Container (http://backend:8000),
// lokal ohne Docker bleibt es http://localhost:8000.
const apiTarget = process.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    proxy: {
      '/api': apiTarget,
    },
  },
})
