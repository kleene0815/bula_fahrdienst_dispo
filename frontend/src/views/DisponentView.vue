<template>
  <div class="disponent-layout">
    <!-- Topbar -->
    <header class="topbar">
      <div class="topbar__stats">
        <span class="stat"><strong>{{ stats.offen }}</strong> offen</span>
        <span class="stat"><strong>{{ stats.unterwegs }}</strong> unterwegs</span>
        <span class="stat"><strong>{{ stats.erledigt }}</strong> erledigt</span>
      </div>
      <div class="topbar__user">
        <span>{{ auth.user?.name }}</span>
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
        <div class="card-list">
          <FahrtKarte
            v-for="trip in sortedTrips"
            :key="trip.id"
            :trip="trip"
            @complete="tripsStore.complete(trip.id)"
            @abort="tripsStore.abort(trip.id)"
            @print="printTrip = trip"
            @edit="editingTrip = trip; showTripForm = true"
            @drop-order="onDropOrderToTrip(trip, $event)"
            @reorder="onReorderTrip(trip, $event)"
            @order-moved="onOrderMoved(trip, $event)"
            @stop-drag-start="draggingStop = $event"
            @stop-drag-end="draggingStop = null"
          />
          <p v-if="tripsStore.trips.length === 0" class="empty">Keine aktiven Fahrten</p>
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
const editingTrip = ref(null)
const printTrip = ref(null)
const activeFilter = ref('alle')
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
  if (!trip.orders.length) return Infinity
  return Math.min(...trip.orders.map((to) => new Date(to.order.deadline).getTime()))
}

const sortedTrips = computed(() =>
  [...tripsStore.trips].sort((a, b) => {
    const statusDiff = (STATUS_ORDER[a.status] ?? 9) - (STATUS_ORDER[b.status] ?? 9)
    if (statusDiff !== 0) return statusDiff
    return earliestDeadline(a) - earliestDeadline(b)
  })
)

const filteredOrders = computed(() => {
  if (activeFilter.value === 'alle') return ordersStore.orders
  return ordersStore.orders.filter((o) => o.status === activeFilter.value)
})

const openOrders = computed(() =>
  ordersStore.orders.filter((o) => o.status === 'offen')
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
  unterwegs: ordersStore.orders.filter((o) => o.status === 'unterwegs').length,
  erledigt: ordersStore.orders.filter((o) => o.status === 'erledigt').length,
}))

function onOrderSaved() {
  showOrderForm.value = false
  editingOrder.value = null
}

function onTripSaved() {
  showTripForm.value = false
  editingTrip.value = null
  preSelectedOrderId.value = null
}

async function onDropOrderToTrip(trip, payload) {
  const orderId = typeof payload === 'string' ? payload : payload.orderId
  const currentIds = trip.orders.map((to) => to.order.id)
  if (currentIds.includes(orderId)) return
  await tripsStore.update(trip.id, { order_ids: [...currentIds, orderId] })
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
  await Promise.all([ordersStore.fetchAll(), tripsStore.fetchAll()])
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
