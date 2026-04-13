import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

// Keycloak initialisieren bevor die App gemountet wird
const auth = useAuthStore()
auth.init().then(() => {
  app.mount('#app')

  // Jetzt sind Rollen bekannt — zur richtigen Standardansicht navigieren.
  // Der Catch-all hat beim Erstzugriff noch keine Rollen gekannt.
  const mobile = window.matchMedia('(max-width: 768px)').matches
  if (auth.isDisponent && !mobile) {
    router.replace({ name: 'disponent' })
  } else if (auth.isFahrer) {
    router.replace({ name: 'fahrer' })
  } else if (auth.isDisponent) {
    router.replace({ name: 'disponent' })
  }
})
