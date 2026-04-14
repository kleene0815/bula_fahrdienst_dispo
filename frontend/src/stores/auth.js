import Keycloak from 'keycloak-js'
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const env = window.__env__ ?? {}

const keycloak = new Keycloak({
  url: env.KEYCLOAK_URL ?? import.meta.env.VITE_KEYCLOAK_URL,
  realm: env.KEYCLOAK_REALM ?? import.meta.env.VITE_KEYCLOAK_REALM,
  clientId: env.KEYCLOAK_CLIENT_ID ?? import.meta.env.VITE_KEYCLOAK_CLIENT_ID,
})

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)   // { id, name, email, roles: [] }
  const token = ref(null)
  const ready = ref(false)

  const isDisponent = computed(() => user.value?.roles.includes('disponent') ?? false)
  const isFahrer = computed(() => user.value?.roles.includes('fahrer') ?? false)

  async function init() {
    const authenticated = await keycloak.init({
      onLoad: 'login-required',
      checkLoginIframe: false,
    })

    if (!authenticated) return

    token.value = keycloak.token

    // Nutzer aus dem Backend laden (erzeugt/aktualisiert den lokalen Eintrag)
    const res = await fetch('/api/v1/users/me', {
      headers: { Authorization: `Bearer ${token.value}` },
    })
    user.value = await res.json()
    ready.value = true

    // Token automatisch erneuern bevor er abläuft
    keycloak.onTokenExpired = () => {
      keycloak.updateToken(60).then(() => {
        token.value = keycloak.token
      })
    }
  }

  async function refreshIfExpired() {
    if (keycloak.isTokenExpired(30)) {
      await keycloak.updateToken(30)
      token.value = keycloak.token
    }
  }

  function logout() {
    keycloak.logout()
  }

  return { user, token, ready, isDisponent, isFahrer, init, refreshIfExpired, logout }
})
