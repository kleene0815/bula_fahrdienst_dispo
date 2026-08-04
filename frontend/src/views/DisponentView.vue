<template>
  <div class="disponent-layout">
    <!-- Topbar -->
    <header class="topbar">
      <div class="topbar__stats">
        <span class="stat"><strong>{{ stats.offen }}</strong> offen</span>
        <span v-if="stats.erwartet" class="stat stat--erwartet"><strong>{{ stats.erwartet }}</strong> erwartete Rückfahrt</span>
        <span class="stat"><strong>{{ stats.unterwegs }}</strong> unterwegs</span>
        <span class="stat"><strong>{{ stats.erledigt }}</strong> erledigt</span>
      </div>
      <div class="topbar__user">
        <span>{{ auth.user?.name }}</span>
        <button v-if="auth.isFahrer" class="btn-ghost" style="margin-left:8px" @click="router.push('/fahrer')">Fahrer-Ansicht</button>
        <button class="btn-ghost" style="margin-left:8px" @click="router.push('/einstellungen')">Einstellungen</button>
        <button class="btn-ghost" style="margin-left:8px" @click="auth.logout()">Abmelden</button>
      </div>
    </header>

    <!-- Hauptbereich -->
    <main class="main-grid">
      <!-- Linke Spalte: Aufträge -->
      <section class="column column--orders">
        <div class="column__header">
          <h2>Aufträge</h2>
          <button class="btn-primary" @click="showOrderForm = true">+ Neuer Auftrag</button>
        </div>
        <div class="filter-bar">
          <button
            v-for="f in statusFilters"
            :key="f.value"
            :class="['filter-btn', { active: activeFilter === f.value }]"
            @click="activeFilter = f.value"
          >{{ f.label }}</button>
        </div>
        <div class="card-list">
          <AuftragKarte
            v-for="order in filteredOrders"
            :key="order.id"
            :order="order"
            @cancel="ordersStore.cancel(order.id)"
            @edit="editingOrder = order; showOrderForm = true"
            @open="onOpenOrder(order)"
          />
          <p v-if="filteredOrders.length === 0" class="empty">Keine Aufträge</p>
        </div>
      </section>

      <!-- Rechte Spalte: Fahrten -->
      <section class="column column--trips">
        <div class="column__header">
          <h2>Fahrten</h2>
          <button class="btn-primary" @click="showTripForm = true">+ Neue Fahrt</button>
        </div>
        <div class="filter-bar">
          <button
            :class="['filter-btn', { active: !showFinishedTrips }]"
            @click="showFinishedTrips = false"
          >Aktive</button>
          <button
            :class="['filter-btn', { active: showFinishedTrips }]"
            @click="showFinishedTrips = true"
          >Alle (inkl. beendete)</button>
        </div>
        <div class="card-list">
          <FahrtKarte
            v-for="trip in visibleTrips"
            :key="trip.id"
            :trip="trip"
            :conflict="tripKonflikte.get(trip.id) ?? null"
            @start="onStartTrip(trip)"
            @complete="onCompleteTrip(trip, $event)"
            @abort="tripsStore.abort(trip.id)"
            @print="printTrip = trip"
            @edit="editingTrip = trip; showTripForm = true"
            @open-fahrer="router.push({ name: 'fahrer', query: { tripId: trip.id } })"
            @drop-order="onDropOrderToTrip(trip, $event)"
            @reorder="onReorderTrip(trip, $event)"
            @order-moved="onOrderMoved(trip, $event)"
            @stop-drag-start="draggingStop = $event"
            @stop-drag-end="draggingStop = null"
          />
          <p v-if="visibleTrips.length === 0" class="empty">{{ showFinishedTrips ? 'Keine Fahrten' : 'Keine aktiven Fahrten' }}</p>
          <div
            class="neue-fahrt-zone"
            :class="{ 'neue-fahrt-zone--active': dragOverNewTrip }"
            @dragover.prevent="dragOverNewTrip = true"
            @dragleave="dragOverNewTrip = false"
            @drop="onDropOrderToNewTrip"
          >+ Neue Fahrt</div>
        </div>
      </section>
    </main>

    <!-- Modals -->
    <AuftragFormModal
      v-if="showOrderForm"
      :order="editingOrder"
      @saved="onOrderSaved"
      @close="showOrderForm = false; editingOrder = null"
    />
    <AuftragFormModal
      v-if="viewingOrder"
      :order="viewingOrder"
      readonly
      @close="viewingOrder = null"
    />
    <FahrtFormModal
      v-if="showTripForm"
      :trip="editingTrip"
      :open-orders="tripFormOrders"
      :pre-selected-order-id="preSelectedOrderId"
      @saved="onTripSaved"
      @close="showTripForm = false; editingTrip = null; preSelectedOrderId = null"
    />
    <AuftragsscheinDruck
      v-if="printTrip"
      :trip="printTrip"
      @close="printTrip = null"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useOrdersStore } from '@/stores/orders'
import { useTripsStore } from '@/stores/trips'
import { api } from '@/api/client'
import AuftragKarte from '@/components/AuftragKarte.vue'
import FahrtKarte from '@/components/FahrtKarte.vue'
import AuftragFormModal from '@/components/AuftragFormModal.vue'
import FahrtFormModal from '@/components/FahrtFormModal.vue'
import AuftragsscheinDruck from '@/components/AuftragsscheinDruck.vue'

const router = useRouter()
const auth = useAuthStore()
const ordersStore = useOrdersStore()
const tripsStore = useTripsStore()

const showOrderForm = ref(false)
const showTripForm = ref(false)
const editingOrder = ref(null)
const viewingOrder = ref(null)
const editingTrip = ref(null)
const printTrip = ref(null)
const activeFilter = ref('offen')
const showFinishedTrips = ref(false)
const preSelectedOrderId = ref(null)
const dragOverNewTrip = ref(false)
const draggingStop = ref(null) // { orderId, sourceTripId } — gesetzt während SortableJS-Drag

const statusFilters = [
  { value: 'alle', label: 'Alle' },
  { value: 'offen', label: 'Offen' },
  { value: 'zugeteilt', label: 'Zugeteilt' },
  { value: 'unterwegs', label: 'Unterwegs' },
  { value: 'erledigt', label: 'Erledigt' },
]

const STATUS_ORDER = { aktiv: 0, geplant: 1, abgeschlossen: 2, abgebrochen: 3 }

function earliestDeadline(trip) {
  const times = trip.orders
    .filter((to) => to.order.deadline)
    .map((to) => new Date(to.order.deadline).getTime())
  return times.length ? Math.min(...times) : Infinity
}

const visibleTrips = computed(() =>
  showFinishedTrips.value
    ? sortedTrips.value
    : sortedTrips.value.filter((t) => ['geplant', 'aktiv'].includes(t.status))
)

const sortedTrips = computed(() =>
  [...tripsStore.trips].sort((a, b) => {
    const statusDiff = (STATUS_ORDER[a.status] ?? 9) - (STATUS_ORDER[b.status] ?? 9)
    if (statusDiff !== 0) return statusDiff
    // Beendete Fahrten: nach Fahrtende absteigend (zuletzt beendete zuerst)
    if (['abgeschlossen', 'abgebrochen'].includes(a.status)) {
      return new Date(b.updated_at) - new Date(a.updated_at)
    }
    const aTime = a.planned_start_time ? new Date(a.planned_start_time).getTime() : Infinity
    const bTime = b.planned_start_time ? new Date(b.planned_start_time).getTime() : Infinity
    if (aTime !== bTime) return aTime - bTime
    return earliestDeadline(a) - earliestDeadline(b)
  })
)

const PUFFER_MINUTEN = 15

function tripEndTime(trip) {
  if (!trip.planned_start_time || !trip.estimated_duration_minutes) return null
  return new Date(trip.planned_start_time).getTime() + trip.estimated_duration_minutes * 60_000
}

const tripKonflikte = computed(() => {
  const aktiveTrips = tripsStore.trips.filter((t) => ['geplant', 'aktiv'].includes(t.status))
  const konflikte = new Map() // trip.id → { reason }

  for (let i = 0; i < aktiveTrips.length; i++) {
    for (let j = 0; j < aktiveTrips.length; j++) {
      if (i === j) continue
      const a = aktiveTrips[i]
      const b = aktiveTrips[j]
      if (!a.planned_start_time || !b.planned_start_time) continue

      const aStart = new Date(a.planned_start_time).getTime()
      const bStart = new Date(b.planned_start_time).getTime()
      if (aStart >= bStart) continue // nur a → b prüfen (a startet zuerst)

      const aEnd = tripEndTime(a)
      if (!aEnd) continue

      const pufferEnde = aEnd + PUFFER_MINUTEN * 60_000
      if (bStart >= pufferEnde) continue // genug Abstand

      const gleicherFahrer = a.driver && b.driver && a.driver.id === b.driver.id
      const gleichesFahrzeug = a.vehicle && b.vehicle && a.vehicle.id === b.vehicle.id
      if (!gleicherFahrer && !gleichesFahrzeug) continue

      const aEndFormatted = new Date(aEnd).toLocaleString('de-DE', { dateStyle: 'short', timeStyle: 'short' })
      const aName = a.name || `Fahrt #${a.trip_number}`
      const parts = []
      if (gleicherFahrer) parts.push(`Fahrer ${a.driver.name}`)
      if (gleichesFahrzeug) parts.push(`Fahrzeug ${a.vehicle.name}`)
      const reason = `${parts.join(' & ')} noch bis ${aEndFormatted} in ${aName} gebunden (< ${PUFFER_MINUTEN} min Puffer)`

      if (!konflikte.has(b.id) || bStart < new Date(konflikte.get(b.id)._aStart).getTime()) {
        konflikte.set(b.id, { reason, _aStart: a.planned_start_time })
      }
    }
  }
  return konflikte
})

const filteredOrders = computed(() => {
  if (activeFilter.value === 'alle') return ordersStore.orders
  if (activeFilter.value === 'offen') {
    // Erwartete Rückfahrten verhalten sich wie offene Aufträge
    return ordersStore.orders.filter((o) => ['offen', 'erwartete_rueckfahrt'].includes(o.status))
  }
  if (activeFilter.value === 'erledigt') {
    // Zuletzt abgeschlossene Aufträge zuerst
    return ordersStore.orders
      .filter((o) => o.status === 'erledigt')
      .sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at))
  }
  return ordersStore.orders.filter((o) => o.status === activeFilter.value)
})

const openOrders = computed(() =>
  ordersStore.orders.filter((o) => ['offen', 'erwartete_rueckfahrt'].includes(o.status))
)

// Für FahrtFormModal: offene Aufträge + ggf. vorausgewählter Auftrag (auch wenn noch zugeteilt)
const tripFormOrders = computed(() => {
  if (!preSelectedOrderId.value) return openOrders.value
  const alreadyIncluded = openOrders.value.some((o) => o.id === preSelectedOrderId.value)
  if (alreadyIncluded) return openOrders.value
  const extra = ordersStore.orders.find((o) => o.id === preSelectedOrderId.value)
  return extra ? [...openOrders.value, extra] : openOrders.value
})

const stats = computed(() => ({
  offen: ordersStore.orders.filter((o) => o.status === 'offen').length,
  erwartet: ordersStore.orders.filter((o) => o.status === 'erwartete_rueckfahrt').length,
  unterwegs: ordersStore.orders.filter((o) => o.status === 'unterwegs').length,
  erledigt: ordersStore.orders.filter((o) => o.status === 'erledigt').length,
}))

function onOrderSaved() {
  showOrderForm.value = false
  editingOrder.value = null
}

async function onStartTrip(trip) {
  try {
    await tripsStore.start(trip.id)
  } catch (e) {
    alert(e.message ?? 'Fahrt konnte nicht gestartet werden')
  }
}

async function onCompleteTrip(trip, force) {
  try {
    await tripsStore.complete(trip.id, force)
  } catch (e) {
    alert(e.message ?? 'Fahrt konnte nicht abgeschlossen werden')
  }
}

function onOpenOrder(order) {
  if (['offen', 'erwartete_rueckfahrt', 'zugeteilt'].includes(order.status)) {
    editingOrder.value = order
    showOrderForm.value = true
  } else {
    viewingOrder.value = order
  }
}

function onTripSaved() {
  showTripForm.value = false
  editingTrip.value = null
  preSelectedOrderId.value = null
}

async function onDropOrderToTrip(trip, payload) {
  const orderId = typeof payload === 'string' ? payload : payload.orderId
  const tripStatus = typeof payload === 'object' ? payload.tripStatus : trip.status
  const currentIds = trip.orders.map((to) => to.order.id)
  if (currentIds.includes(orderId)) return

  try {
    if (tripStatus === 'aktiv') {
      const confirmed = confirm(
        `Die Fahrt "${trip.name || 'Fahrt #' + trip.trip_number}" ist bereits gestartet.\n\nDen Auftrag trotzdem hinzufügen? Der Fahrer sieht ihn sofort als neuen Stopp.`
      )
      if (!confirmed) return
      await tripsStore.addOrder(trip.id, orderId)
    } else {
      await tripsStore.update(trip.id, { order_ids: [...currentIds, orderId] })
    }
  } catch (e) {
    alert(e.message ?? 'Auftrag konnte nicht zugeteilt werden')
  }
}

async function onReorderTrip(trip, orderIds) {
  await tripsStore.update(trip.id, { order_ids: orderIds })
}

async function onOrderMoved(targetTrip, { orderId, sourceTripId, newOrderIds }) {
  // Zuerst aus der Quell-Fahrt entfernen, dann Ziel-Fahrt aktualisieren
  if (sourceTripId) {
    const sourceTrip = tripsStore.trips.find((t) => t.id === sourceTripId)
    if (sourceTrip) {
      const remainingIds = sourceTrip.orders
        .filter((to) => to.order.id !== orderId)
        .map((to) => to.order.id)
      await tripsStore.update(sourceTripId, { order_ids: remainingIds })
    }
  }
  await tripsStore.update(targetTrip.id, { order_ids: newOrderIds })
}

async function onDropOrderToNewTrip(event) {
  dragOverNewTrip.value = false

  let orderId, sourceTripId

  if (draggingStop.value) {
    // Stopp aus einer Fahrt (SortableJS-Drag) — dataTransfer nicht zuverlässig
    orderId = draggingStop.value.orderId
    sourceTripId = draggingStop.value.sourceTripId
    draggingStop.value = null
  } else {
    // Auftragskarte aus der linken Spalte (nativer HTML5-Drag)
    orderId = event.dataTransfer.getData('order-id')
    if (!orderId) return
    // Auftrag könnte bereits zugeteilt sein — dann aus der aktuellen Fahrt entfernen
    const sourceTrip = tripsStore.trips.find((t) =>
      t.orders.some((to) => to.order.id === orderId)
    )
    sourceTripId = sourceTrip?.id ?? null
  }

  if (!orderId) return

  if (sourceTripId) {
    const sourceTrip = tripsStore.trips.find((t) => t.id === sourceTripId)
    if (sourceTrip) {
      const remainingIds = sourceTrip.orders
        .filter((to) => to.order.id !== orderId)
        .map((to) => to.order.id)
      await tripsStore.update(sourceTripId, { order_ids: remainingIds })
    }
  }

  preSelectedOrderId.value = orderId
  showTripForm.value = true
}

// SSE
let eventSource = null

async function connectSSE() {
  eventSource = await api.sse('/events')
  eventSource.addEventListener('order_created', (e) => ordersStore.applyEvent('order_created', JSON.parse(e.data)))
  eventSource.addEventListener('order_updated', (e) => ordersStore.applyEvent('order_updated', JSON.parse(e.data)))
  eventSource.addEventListener('trip_created', (e) => tripsStore.applyEvent('trip_created', JSON.parse(e.data)))
  eventSource.addEventListener('trip_updated', (e) => tripsStore.applyEvent('trip_updated', JSON.parse(e.data)))
}

onMounted(async () => {
  await Promise.all([ordersStore.fetchAll(), tripsStore.fetchAll(true)])
  await connectSSE()
})

onUnmounted(() => {
  eventSource?.close()
})
</script>

<style scoped>
.disponent-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 20px;
  background: #fff;
  border-bottom: 1px solid #e0e0e0;
  flex-shrink: 0;
}
.topbar__stats { display: flex; gap: 20px; }
.stat { color: #555; font-size: 13px; }
.stat--erwartet { color: #6a1b9a; }
.topbar__user { display: flex; align-items: center; }

.main-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0;
  flex: 1;
  overflow: hidden;
}

.column {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-right: 1px solid #e0e0e0;
}
.column--trips { border-right: none; }

.column__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid #e0e0e0;
  background: #fafafa;
}
.column__header h2 { font-size: 16px; }

.filter-bar {
  display: flex;
  gap: 4px;
  padding: 8px 16px;
  border-bottom: 1px solid #eee;
  background: #fff;
}
.filter-btn {
  background: transparent;
  border: 1px solid #ddd;
  border-radius: 12px;
  padding: 3px 10px;
  font-size: 12px;
  color: #555;
}
.filter-btn.active {
  background: #1565c0;
  color: #fff;
  border-color: #1565c0;
}

.card-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.empty { color: #aaa; font-size: 13px; text-align: center; padding: 20px 0; }

.neue-fahrt-zone {
  border: 2px dashed #ccc;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
  color: #aaa;
  font-size: 13px;
  transition: border-color .15s, color .15s, background .15s;
}
.neue-fahrt-zone--active {
  border-color: #1565c0;
  color: #1565c0;
  background: #e3f2fd;
}
</style>
