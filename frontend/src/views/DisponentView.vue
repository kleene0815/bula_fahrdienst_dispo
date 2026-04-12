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
            v-for="trip in tripsStore.trips"
            :key="trip.id"
            :trip="trip"
            @complete="tripsStore.complete(trip.id)"
            @abort="tripsStore.abort(trip.id)"
            @print="printTrip = trip"
            @edit="editingTrip = trip; showTripForm = true"
          />
          <p v-if="tripsStore.trips.length === 0" class="empty">Keine aktiven Fahrten</p>
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
      :open-orders="openOrders"
      @saved="onTripSaved"
      @close="showTripForm = false; editingTrip = null"
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

const statusFilters = [
  { value: 'alle', label: 'Alle' },
  { value: 'offen', label: 'Offen' },
  { value: 'zugeteilt', label: 'Zugeteilt' },
  { value: 'unterwegs', label: 'Unterwegs' },
  { value: 'erledigt', label: 'Erledigt' },
]

const filteredOrders = computed(() => {
  if (activeFilter.value === 'alle') return ordersStore.orders
  return ordersStore.orders.filter((o) => o.status === activeFilter.value)
})

const openOrders = computed(() =>
  ordersStore.orders.filter((o) => o.status === 'offen')
)

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
</style>
