<template>
  <div class="fahrer-layout">
    <header class="fahrer-header">
      <h1>Meine Fahrten</h1>
      <div style="display:flex;gap:8px">
        <button v-if="auth.isDisponent" class="btn-ghost" style="font-size:13px" @click="router.push('/disponent')">Disponent-Ansicht</button>
        <button class="btn-ghost" style="font-size:13px" @click="auth.logout()">Abmelden</button>
      </div>
    </header>

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
  if (!trip.orders.length) return Infinity
  return Math.min(...trip.orders.map((to) => new Date(to.order.deadline).getTime()))
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

onMounted(async () => {
  await load()
  await connectSSE()
})
</script>

<style scoped>
.fahrer-layout { display:flex;flex-direction:column;min-height:100vh;background:#f5f5f5; }
.fahrer-header { display:flex;align-items:center;justify-content:space-between;padding:14px 16px;background:#fff;border-bottom:1px solid #e0e0e0; }
.fahrer-header h1 { font-size:18px; }
.fahrt-detail { flex:1;padding:16px; }
.vertretung-banner {
  max-width:560px;margin:0 auto 12px;
  background:#f3e5f5;color:#6a1b9a;
  border:1px solid #ce93d8;border-radius:8px;
  padding:10px 14px;font-size:13px;
}
.no-trips { flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#aaa; }
</style>
