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
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useTripsStore } from '@/stores/trips'
import FahrtDetail from '@/components/FahrtDetail.vue'

const auth = useAuthStore()
const tripsStore = useTripsStore()
const route = useRoute()
const router = useRouter()
const loading = ref(true)
const completedMessage = ref(null)

function earliestDeadline(trip) {
  if (!trip.orders.length) return Infinity
  return Math.min(...trip.orders.map((to) => new Date(to.order.deadline).getTime()))
}

// Wenn via QR-Code eine spezifische Fahrt-ID übergeben wurde, diese zuerst anzeigen
const activeTrip = computed(() => {
  const trips = [...tripsStore.myTrips].sort((a, b) => {
    const statusOrder = { aktiv: 0, geplant: 1, abgeschlossen: 2, abgebrochen: 3 }
    const statusDiff = (statusOrder[a.status] ?? 9) - (statusOrder[b.status] ?? 9)
    if (statusDiff !== 0) return statusDiff
    return earliestDeadline(a) - earliestDeadline(b)
  })
  if (route.query.tripId) {
    return trips.find((t) => t.id === route.query.tripId) ?? trips[0] ?? null
  }
  return trips.find((t) => t.status === 'aktiv') ?? trips[0] ?? null
})

async function load() {
  loading.value = true
  await tripsStore.fetchMine()
  loading.value = false
}

async function onComplete() {
  await tripsStore.complete(activeTrip.value.id)
  // Nach Abschluss kurze Bestätigung
  completedMessage.value = `Fahrt abgeschlossen — ${activeTrip.value.vehicle?.name} und du bist wieder frei.`
  await tripsStore.fetchMine()
}

onMounted(load)
</script>

<style scoped>
.fahrer-layout { display:flex;flex-direction:column;min-height:100vh;background:#f5f5f5; }
.fahrer-header { display:flex;align-items:center;justify-content:space-between;padding:14px 16px;background:#fff;border-bottom:1px solid #e0e0e0; }
.fahrer-header h1 { font-size:18px; }
.fahrt-detail { flex:1;padding:16px; }
.no-trips { flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#aaa; }
</style>
