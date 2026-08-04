<template>
  <div class="fahrer-layout">
    <header class="fahrer-header">
      <h1>Meine Fahrten</h1>
      <div style="display:flex;gap:8px">
        <button v-if="auth.isDisponent" class="btn-ghost" style="font-size:13px" @click="router.push('/disponent')">Disponent-Ansicht</button>
        <button class="btn-ghost" style="font-size:13px" @click="auth.logout()">Abmelden</button>
      </div>
    </header>

    <div v-if="securityPhone" class="security-bar">
      🛡 Sicherheitszentrale: <a :href="`tel:${securityPhone}`">{{ securityPhone }}</a>
    </div>

    <div v-if="needsPhone" class="phone-box">
      <strong>📞 Telefonnummer fehlt</strong>
      <p>Damit dich die Disposition erreichen kann, hinterlege bitte deine Telefonnummer.</p>
      <form class="phone-box__form" @submit.prevent="savePhone">
        <input v-model="phoneInput" type="tel" placeholder="z.B. 0171 1234567" required />
        <button type="submit" class="btn-primary" :disabled="phoneSaving">
          {{ phoneSaving ? 'Speichern…' : 'Speichern' }}
        </button>
      </form>
      <p v-if="phoneError" class="phone-box__error">{{ phoneError }}</p>
    </div>

    <div v-if="loading" class="loading-screen">Laden…</div>

    <div v-else-if="activeTrip" class="fahrt-detail">
      <div v-if="isVertretung" class="vertretung-banner">
        🔄 Vertretung: Du bearbeitest diese Fahrt anstelle von
        <strong>{{ activeTrip.driver?.name ?? '– kein Fahrer zugeteilt –' }}</strong>
      </div>
      <FahrtDetail
        :trip="activeTrip"
        @start="tripsStore.start(activeTrip.id)"
        @complete-stop="(orderId) => tripsStore.completeStop(activeTrip.id, orderId)"
        @complete="onComplete"
      />
    </div>

    <div v-else class="no-trips">
      <p>Keine aktiven Fahrten.</p>
      <button class="btn-ghost" style="margin-top:16px" @click="load">Aktualisieren</button>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useTripsStore } from '@/stores/trips'
import { api } from '@/api/client'
import FahrtDetail from '@/components/FahrtDetail.vue'

const auth = useAuthStore()
const tripsStore = useTripsStore()
const route = useRoute()
const router = useRouter()
const loading = ref(true)
const completedMessage = ref(null)
const vertretungTrip = ref(null) // Fremde Fahrt, die ein Disponent in Vertretung geöffnet hat

function earliestDeadline(trip) {
  const times = trip.orders
    .filter((to) => to.order.deadline)
    .map((to) => new Date(to.order.deadline).getTime())
  return times.length ? Math.min(...times) : Infinity
}

// Wenn via QR-Code oder Disponent-Vertretung eine spezifische Fahrt-ID übergeben wurde, diese zuerst anzeigen
const activeTrip = computed(() => {
  const trips = [...tripsStore.myTrips].sort((a, b) => {
    const statusOrder = { aktiv: 0, geplant: 1, abgeschlossen: 2, abgebrochen: 3 }
    const statusDiff = (statusOrder[a.status] ?? 9) - (statusOrder[b.status] ?? 9)
    if (statusDiff !== 0) return statusDiff
    return earliestDeadline(a) - earliestDeadline(b)
  })
  if (route.query.tripId) {
    return trips.find((t) => t.id === route.query.tripId) ?? vertretungTrip.value ?? trips[0] ?? null
  }
  return trips.find((t) => t.status === 'aktiv') ?? trips[0] ?? null
})

const isVertretung = computed(() =>
  activeTrip.value != null && activeTrip.value.driver?.id !== auth.user?.id
)

// Rote Box, solange der eingeloggte Fahrer keine Telefonnummer hinterlegt hat
const phoneInput = ref('')
const phoneSaving = ref(false)
const phoneError = ref(null)

const needsPhone = computed(() =>
  auth.isFahrer && auth.user != null && !auth.user.phone
)

async function savePhone() {
  phoneSaving.value = true
  phoneError.value = null
  try {
    auth.user = await api.patch('/users/me', { phone: phoneInput.value })
  } catch (e) {
    phoneError.value = e.message ?? 'Speichern fehlgeschlagen'
  } finally {
    phoneSaving.value = false
  }
}

async function load() {
  loading.value = true
  await tripsStore.fetchMine()
  if (route.query.tripId && !tripsStore.myTrips.some((t) => t.id === route.query.tripId)) {
    try {
      vertretungTrip.value = await tripsStore.fetchOne(route.query.tripId)
    } catch {
      vertretungTrip.value = null
    }
  }
  loading.value = false
}

let eventSource = null

async function connectSSE() {
  eventSource = await api.sse('/events')
  eventSource.addEventListener('trip_updated', (e) => {
    const data = JSON.parse(e.data)
    tripsStore.applyEvent('trip_updated', data)
    if (vertretungTrip.value && data.id === vertretungTrip.value.id) {
      vertretungTrip.value = data
    }
  })
}

onUnmounted(() => {
  if (eventSource) eventSource.close()
})

async function onComplete() {
  await tripsStore.complete(activeTrip.value.id)
  // Nach Abschluss kurze Bestätigung
  completedMessage.value = `Fahrt abgeschlossen — ${activeTrip.value.vehicle?.name} und du bist wieder frei.`
  await tripsStore.fetchMine()
}

// Telefonnummer der Sicherheitszentrale — unabhängig von Fahraufträgen immer sichtbar
const securityPhone = ref('')

async function loadSecurityPhone() {
  try {
    const cfg = await api.get('/config/public')
    securityPhone.value = cfg.security_center_phone ?? ''
  } catch {
    securityPhone.value = ''
  }
}

onMounted(async () => {
  await Promise.all([load(), loadSecurityPhone()])
  await connectSSE()
})
</script>

<style scoped>
.fahrer-layout { display:flex;flex-direction:column;min-height:100vh;background:#f5f5f5; }
.fahrer-header { display:flex;align-items:center;justify-content:space-between;padding:14px 16px;background:#fff;border-bottom:1px solid #e0e0e0; }
.fahrer-header h1 { font-size:18px; }
.fahrt-detail { flex:1;padding:16px; }
.security-bar {
  background:#fff8e1;color:#795548;
  border-bottom:1px solid #ffe082;
  padding:8px 16px;font-size:13px;
  text-align:center;
}
.security-bar a { color:#1565c0;font-weight:600;text-decoration:none; }
.phone-box {
  max-width:560px;margin:16px auto 0;
  background:#ffebee;color:#b71c1c;
  border:1px solid #ef9a9a;border-radius:8px;
  padding:14px 16px;font-size:14px;
  width:calc(100% - 32px);
}
.phone-box p { margin:6px 0 10px;font-size:13px; }
.phone-box__form { display:flex;gap:8px; }
.phone-box__form input { flex:1;padding:8px 10px;border:1px solid #ef9a9a;border-radius:6px;font-size:14px; }
.phone-box__error { color:#c62828;font-size:12px;margin-top:6px; }
.vertretung-banner {
  max-width:560px;margin:0 auto 12px;
  background:#f3e5f5;color:#6a1b9a;
  border:1px solid #ce93d8;border-radius:8px;
  padding:10px 14px;font-size:13px;
}
.no-trips { flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#aaa; }
</style>
