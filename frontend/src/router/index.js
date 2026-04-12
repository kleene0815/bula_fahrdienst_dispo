import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      // QR-Code-Einstieg: immer zuerst prüfen
      path: '/trip/:qrToken',
      name: 'trip-redirect',
      component: () => import('@/views/TripRedirectView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/disponent',
      name: 'disponent',
      component: () => import('@/views/DisponentView.vue'),
      meta: { requiresAuth: true, requiresRole: 'disponent' },
    },
    {
      path: '/fahrer',
      name: 'fahrer',
      component: () => import('@/views/FahrerView.vue'),
      meta: { requiresAuth: true, requiresRole: 'fahrer' },
    },
    {
      path: '/einstellungen',
      name: 'einstellungen',
      component: () => import('@/views/EinstellungenView.vue'),
      meta: { requiresAuth: true, requiresRole: 'disponent' },
    },
    {
      // Catch-all: Weiterleitung zur passenden Standardansicht
      path: '/:pathMatch(.*)*',
      redirect: () => {
        const auth = useAuthStore()
        return defaultRoute(auth)
      },
    },
  ],
})

function defaultRoute(auth) {
  const mobile = window.matchMedia('(max-width: 768px)').matches
  if (auth.isDisponent && !mobile) return { name: 'disponent' }
  if (auth.isFahrer) return { name: 'fahrer' }
  if (auth.isDisponent) return { name: 'disponent' }
  return { name: 'fahrer' }
}

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (!auth.ready) return true  // Keycloak übernimmt Login, App ist noch nicht initialisiert

  if (to.meta.requiresRole === 'disponent' && !auth.isDisponent) {
    return defaultRoute(auth)
  }
  if (to.meta.requiresRole === 'fahrer' && !auth.isFahrer) {
    return defaultRoute(auth)
  }
})

export default router
