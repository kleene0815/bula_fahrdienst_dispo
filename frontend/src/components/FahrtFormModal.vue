<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal">
      <div class="modal__header">
        <h3>{{ trip ? 'Fahrt bearbeiten' : 'Neue Fahrt' }}</h3>
        <button class="btn-ghost" @click="$emit('close')">✕</button>
      </div>
      <div class="modal__body">
        <!-- Name -->
        <section class="section">
          <h4>Name <span class="optional">(optional)</span></h4>
          <input v-model="form.name" type="text" placeholder="Fahrt #wird automatisch vergeben" />
        </section>

        <!-- Fahrer -->
        <section class="section">
          <h4>Fahrer <span class="optional">(optional)</span></h4>
          <div class="driver-combobox" @focusout="onDriverFocusOut">
            <button type="button" class="driver-trigger" @click="toggleDriverDropdown">
              <span :class="{ 'driver-trigger__placeholder': !form.driver_id }">{{ selectedDriverName }}</span>
              <span class="driver-trigger__arrow">▾</span>
            </button>
            <div v-if="driverDropdownOpen" class="driver-dropdown">
              <input
                ref="driverSearchInput"
                v-model="driverSearch"
                class="driver-search"
                placeholder="Suchen…"
                @keydown.escape="driverDropdownOpen = false"
              />
              <div class="driver-list">
                <button type="button" class="driver-option" :class="{ selected: form.driver_id === null }" @click="selectDriver(null)">– kein Fahrer –</button>
                <button
                  v-for="u in filteredUsers"
                  :key="u.id"
                  type="button"
                  class="driver-option"
                  :class="{ selected: form.driver_id === u.id }"
                  @click="selectDriver(u.id)"
                >{{ u.name }}</button>
                <p v-if="filteredUsers.length === 0" class="driver-empty">Kein Fahrer gefunden</p>
              </div>
            </div>
          </div>
        </section>

        <!-- Fahrzeug -->
        <section class="section">
          <h4>Fahrzeug <span class="optional">(optional)</span></h4>
          <div class="card-grid">
            <button
              v-for="v in vehiclesStore.vehicles"
              :key="v.id"
              class="select-card"
              :class="{ selected: form.vehicle_id === v.id }"
              type="button"
              @click="form.vehicle_id = form.vehicle_id === v.id ? null : v.id"
            >
              <strong>{{ v.name }}</strong>
              <small>{{ v.license_plate }} · {{ v.seats }} Sitze</small>
            </button>
          </div>
        </section>

        <!-- Aufträge (Drag & Drop) -->
        <section class="section">
          <h4>Aufträge</h4>
          <div class="orders-layout">

            <!-- Ausgewählte Aufträge (sortierbar per D&D) -->
            <div class="orders-col">
              <p class="orders-col__label">Reihenfolge in der Fahrt</p>
              <VueDraggable
                v-model="selectedOrderObjects"
                :animation="150"
                :group="{ name: 'fahrt-orders' }"
                class="drop-zone drop-zone--selected"
              >
                <div
                  v-for="(o, idx) in selectedOrderObjects"
                  :key="o.id"
                  class="order-item order-item--selected"
                >
                  <span class="order-num">{{ idx + 1 }}</span>
                  <span class="order-item__label">
                    <strong>{{ o.destination }}</strong>
                    <small>{{ formatTime(o.deadline) }} · {{ o.trip_type }}</small>
                    <small v-if="o.patient_name">👤 {{ o.patient_name }}<span v-if="o.companion"> +1</span></small>
                  </span>
                </div>
                <p v-if="selectedOrderObjects.length === 0" class="drop-hint">
                  Aufträge von rechts hierher ziehen
                </p>
              </VueDraggable>
            </div>

            <!-- Verfügbare Aufträge -->
            <div class="orders-col">
              <p class="orders-col__label">Verfügbare Aufträge</p>
              <VueDraggable
                v-model="availableOrderObjects"
                :animation="150"
                :group="{ name: 'fahrt-orders' }"
                :sort="false"
                class="drop-zone"
              >
                <div
                  v-for="o in availableOrderObjects"
                  :key="o.id"
                  class="order-item"
                >
                  <span class="order-item__label">
                    <strong>{{ o.destination }}</strong>
                    <small>{{ formatTime(o.deadline) }} · {{ o.trip_type }}</small>
                    <small v-if="o.patient_name">👤 {{ o.patient_name }}<span v-if="o.companion"> +1</span></small>
                  </span>
                </div>
                <p v-if="availableOrderObjects.length === 0" class="drop-hint drop-hint--muted">
                  Keine weiteren Aufträge
                </p>
              </VueDraggable>
            </div>

          </div>
        </section>

        <!-- Kapazität (nur wenn Fahrzeug gewählt) -->
        <section v-if="form.vehicle_id" class="section">
          <h4>Kapazität</h4>
          <div class="kapazitaet">
            <div class="kapazitaet__bar">
              <div
                class="kapazitaet__fill"
                :class="{ warn: seatRatio > 0.7, over: seatRatio > 1 }"
                :style="{ width: Math.min(seatRatio * 100, 100) + '%' }"
              ></div>
            </div>
            <span :class="{ 'over-text': seatRatio > 1 }">{{ usedSeats }} / {{ selectedVehicleSeats }} Sitze</span>
          </div>
          <p v-if="seatRatio > 1" class="error">Kapazität überschritten — Speichern nicht möglich</p>
        </section>

        <!-- Startzeit -->
        <section class="section">
          <h4>Geplante Startzeit</h4>
          <div class="routing-row">
            <template v-if="trip?.planned_start_time || previewRoute?.planned_start_time">
              <span class="routing-info">
                🕐 <strong>{{ formatTime(trip?.planned_start_time ?? previewRoute.planned_start_time) }}</strong>
                <span v-if="trip?.estimated_duration_minutes ?? previewRoute?.estimated_duration_minutes"> · ~{{ trip?.estimated_duration_minutes ?? previewRoute?.estimated_duration_minutes }} min</span>
                <span v-if="trip?.start_time_manual_override" class="routing-manual-badge">Manuell</span>
              </span>
              <button v-if="trip?.start_time_manual_override" type="button" class="btn-ghost" style="font-size:12px;padding:3px 8px" @click="onClearOverride">Auto</button>
            </template>
            <span v-else class="routing-info routing-info--muted">Noch nicht berechnet</span>
            <button v-if="!routingCalculating" type="button" class="btn-ghost" style="font-size:12px;padding:3px 8px" @click="onCalculateRoute" :disabled="selectedOrderObjects.length === 0">🔄 Berechnen</button>
            <span v-else style="font-size:12px;color:#888">Berechne…</span>
          </div>
          <div v-if="trip" style="display:flex;align-items:center;gap:8px;margin-top:8px">
            <label style="font-size:12px;color:#666;white-space:nowrap">Manuell überschreiben:</label>
            <input type="datetime-local" v-model="manualStartTime" style="font-size:12px;flex:1" @change="onSetManualStartTime" />
          </div>
          <p v-if="routingError" class="error" style="margin-top:6px">{{ routingError }}</p>
        </section>

        <!-- Bemerkungen -->
        <section class="section">
          <h4>Bemerkungen</h4>
          <textarea v-model="form.notes" rows="2" placeholder="Hinweise für den Fahrer"></textarea>
        </section>

        <p v-if="error" class="error">{{ error }}</p>
      </div>
      <div class="modal__footer">
        <button class="btn-ghost" @click="$emit('close')">Abbrechen</button>
        <button class="btn-primary" :disabled="saving || seatRatio > 1 || !canSave" @click="submit">
          {{ saving ? 'Wird gespeichert…' : 'Speichern' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { VueDraggable } from 'vue-draggable-plus'
import { useTripsStore } from '@/stores/trips'
import { useVehiclesStore } from '@/stores/vehicles'
import { api } from '@/api/client'
import { computeNeededSeats } from '@/utils/seatOccupancy'

const props = defineProps({ trip: Object, openOrders: Array, preSelectedOrderId: String })
const emit = defineEmits(['saved', 'close'])

// Alle wählbaren Aufträge: bestehende Aufträge der Fahrt + offene Aufträge
const selectableOrders = computed(() => {
  if (!props.trip) return props.openOrders ?? []
  const tripOrderIds = new Set(props.trip.orders.map((to) => to.order.id))
  const tripOrders = props.trip.orders.map((to) => to.order)
  const additionalOpen = (props.openOrders ?? []).filter((o) => !tripOrderIds.has(o.id))
  return [...tripOrders, ...additionalOpen]
})

const tripsStore = useTripsStore()
const vehiclesStore = useVehiclesStore()
const users = ref([])
const driverSearch = ref('')
const driverDropdownOpen = ref(false)
const driverSearchInput = ref(null)

const filteredUsers = computed(() => {
  const q = driverSearch.value.trim().toLowerCase()
  return q ? users.value.filter((u) => u.name.toLowerCase().includes(q)) : users.value
})

const selectedDriverName = computed(() => {
  if (!form.driver_id) return '– kein Fahrer –'
  return users.value.find((u) => u.id === form.driver_id)?.name ?? '– kein Fahrer –'
})

async function toggleDriverDropdown() {
  driverDropdownOpen.value = !driverDropdownOpen.value
  if (driverDropdownOpen.value) {
    driverSearch.value = ''
    await nextTick()
    driverSearchInput.value?.focus()
  }
}

function selectDriver(id) {
  form.driver_id = id
  driverDropdownOpen.value = false
}

function onDriverFocusOut(e) {
  if (!e.currentTarget.contains(e.relatedTarget)) {
    driverDropdownOpen.value = false
  }
}

const saving = ref(false)
const error = ref(null)
const routingCalculating = ref(false)
const routingError = ref(null)
const previewRoute = ref(null) // { planned_start_time, estimated_duration_minutes } für neue Fahrten
const manualStartTime = ref(
  props.trip?.planned_start_time
    ? props.trip.planned_start_time.slice(0, 16)
    : ''
)

watch(
  () => props.trip?.planned_start_time,
  (val) => { manualStartTime.value = val ? val.slice(0, 16) : '' },
)


const form = reactive({
  name: props.trip?.name ?? '',
  driver_id: props.trip?.driver?.id ?? null,
  vehicle_id: props.trip?.vehicle?.id ?? null,
  notes: props.trip?.notes ?? '',
})

// Ausgewählte Aufträge als Objekte (Reihenfolge = sort_order)
const initialSelectedIds = props.trip
  ? [...props.trip.orders]
      .sort((a, b) => a.sort_order - b.sort_order)
      .map((to) => to.order.id)
  : []
if (props.preSelectedOrderId && !initialSelectedIds.includes(props.preSelectedOrderId)) {
  initialSelectedIds.push(props.preSelectedOrderId)
}

const selectedOrderObjects = ref(
  initialSelectedIds
    .map((id) => selectableOrders.value.find((o) => o.id === id))
    .filter(Boolean)
)

const availableOrderObjects = ref(
  selectableOrders.value.filter(
    (o) => !initialSelectedIds.includes(o.id)
  )
)

// Bei Änderungen der Auftragsreihenfolge/-auswahl Startzeit neu berechnen.
watch(
  selectedOrderObjects,
  async () => {
    if (selectedOrderObjects.value.length === 0) return
    const orderIds = selectedOrderObjects.value.map((o) => o.id)
    try {
      if (props.trip) {
        // Bestehende Fahrt: direkt speichern und neu berechnen
        await tripsStore.update(props.trip.id, { order_ids: orderIds })
      } else {
        // Neue Fahrt: Preview-Berechnung ohne Speichern
        const result = await api.post('/trips/preview_route', { order_ids: orderIds })
        previewRoute.value = result
        if (result.planned_start_time) {
          manualStartTime.value = result.planned_start_time.slice(0, 16)
        }
      }
    } catch {
      // Fehler ignorieren – der Nutzer kann manuell speichern
    }
  },
  { deep: true },
)

// Kapazitätsberechnung: Spitzenbelegung über die Fahrtabschnitte in Stopp-Reihenfolge
const usedSeats = computed(() => computeNeededSeats(selectedOrderObjects.value))

const selectedVehicle = computed(() =>
  vehiclesStore.vehicles.find((v) => v.id === form.vehicle_id)
)
const selectedVehicleSeats = computed(() => selectedVehicle.value?.seats ?? '?')
const seatRatio = computed(() =>
  selectedVehicle.value ? usedSeats.value / selectedVehicle.value.seats : 0
)
const canSave = computed(() => selectedOrderObjects.value.length > 0)

async function submit() {
  saving.value = true
  error.value = null
  try {
    const payload = {
      name: form.name || null,
      driver_id: form.driver_id,
      vehicle_id: form.vehicle_id,
      order_ids: selectedOrderObjects.value.map((o) => o.id),
      notes: form.notes || null,
    }
    if (props.trip) {
      await tripsStore.update(props.trip.id, payload)
    } else {
      await tripsStore.create(payload)
    }
    emit('saved')
  } catch (e) {
    error.value = e.message
  } finally {
    saving.value = false
  }
}

function formatTime(iso) {
  if (!iso) return 'keine Deadline'
  return new Date(iso).toLocaleString('de-DE', { dateStyle: 'short', timeStyle: 'short' })
}

async function onCalculateRoute() {
  if (selectedOrderObjects.value.length === 0) return
  routingCalculating.value = true
  routingError.value = null
  try {
    if (!props.trip) {
      const result = await api.post('/trips/preview_route', {
        order_ids: selectedOrderObjects.value.map((o) => o.id),
      })
      previewRoute.value = result
      if (result.planned_start_time) manualStartTime.value = result.planned_start_time.slice(0, 16)
      return
    }
    await tripsStore.calculateRoute(props.trip.id)
  } catch (e) {
    routingError.value = e.message ?? 'Berechnung fehlgeschlagen'
  } finally {
    routingCalculating.value = false
  }
}

async function onSetManualStartTime() {
  if (!props.trip || !manualStartTime.value) return
  await tripsStore.setPlannedStartTime(props.trip.id, manualStartTime.value + ':00')
}

async function onClearOverride() {
  if (!props.trip) return
  await tripsStore.clearStartTimeOverride(props.trip.id)
  manualStartTime.value = ''
}

onMounted(async () => {
  await Promise.all([
    vehiclesStore.fetchAll(),
    api.get('/users').then((u) => { users.value = u }),
  ])
})
</script>

<style scoped>
.modal-overlay { position:fixed;inset:0;background:rgba(0,0,0,.4);display:flex;align-items:center;justify-content:center;z-index:100; }
.modal { background:#fff;border-radius:10px;width:700px;max-width:95vw;max-height:90vh;display:flex;flex-direction:column;box-shadow:0 8px 32px rgba(0,0,0,.2); }
.modal__header { display:flex;align-items:center;justify-content:space-between;padding:16px 20px;border-bottom:1px solid #eee; }
.modal__body { padding:20px;overflow-y:auto;flex:1; }
.modal__footer { display:flex;justify-content:flex-end;gap:10px;padding:16px 20px;border-top:1px solid #eee; }

.section { margin-bottom:20px; }
.section h4 { font-size:13px;font-weight:600;color:#555;margin-bottom:8px;text-transform:uppercase;letter-spacing:.5px; }
.optional { font-weight:400;color:#aaa;text-transform:none;letter-spacing:0; }

.card-grid { display:flex;flex-wrap:wrap;gap:8px; }
.select-card {
  padding:8px 12px;border-radius:6px;border:1px solid #ddd;
  background:#fafafa;cursor:pointer;text-align:left;
  display:flex;flex-direction:column;gap:2px;
}
.select-card.selected { border-color:#1565c0;background:#e3f2fd; }
.select-card small { font-size:11px;color:#888; }

/* Auftrags-Layout */
.orders-layout { display:grid;grid-template-columns:1fr 1fr;gap:12px; }
.orders-col__label { font-size:11px;color:#888;margin-bottom:6px;font-weight:500; }

.drop-zone {
  min-height:100px;border-radius:6px;border:1px dashed #ddd;
  padding:6px;display:flex;flex-direction:column;gap:4px;
}
.drop-zone--selected { border-color:#c5d9f1;background:#fafcff; }

.order-item {
  display:flex;align-items:flex-start;gap:8px;
  padding:7px 8px;border-radius:5px;
  background:#fff;border:1px solid #eee;
  user-select:none;cursor:grab;
}
.order-item:active { cursor:grabbing; }
.order-item--selected { background:#f0f7ff;border-color:#c5d9f1; }

.order-num {
  width:20px;height:20px;border-radius:50%;background:#1565c0;color:#fff;
  display:flex;align-items:center;justify-content:center;
  font-size:11px;font-weight:600;flex-shrink:0;margin-top:1px;
}

.order-item__label { display:flex;flex-direction:column;gap:2px;flex:1;min-width:0; }
.order-item__label strong { font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis; }
.order-item__label small { color:#888;font-size:11px; }

.drop-hint { font-size:12px;color:#bbb;text-align:center;padding:20px 8px;margin:0; }
.drop-hint--muted { color:#ddd; }

.kapazitaet { display:flex;align-items:center;gap:10px;margin-bottom:6px; }
.kapazitaet__bar { flex:1;height:8px;background:#eee;border-radius:4px;overflow:hidden; }
.kapazitaet__fill { height:100%;background:#1565c0;border-radius:4px;transition:width .3s; }
.kapazitaet__fill.warn { background:#e65100; }
.kapazitaet__fill.over { background:#c62828; }
.over-text { color:#c62828;font-weight:600; }
.error { color:#c62828;font-size:13px;margin-top:4px; }

.driver-combobox { position:relative;width:100%; }
.driver-trigger {
  width:100%;display:flex;align-items:center;justify-content:space-between;
  padding:8px 12px;border-radius:6px;border:1px solid #ddd;
  background:#fafafa;cursor:pointer;text-align:left;font-size:14px;
}
.driver-trigger:hover { border-color:#aaa; }
.driver-trigger__placeholder { color:#aaa; }
.driver-trigger__arrow { color:#999;font-size:11px;margin-left:8px; }
.driver-dropdown {
  position:absolute;top:calc(100% + 4px);left:0;right:0;z-index:200;
  background:#fff;border:1px solid #ddd;border-radius:6px;
  box-shadow:0 4px 16px rgba(0,0,0,.12);overflow:hidden;
}
.driver-search {
  width:100%;box-sizing:border-box;padding:8px 12px;
  border:none;border-bottom:1px solid #eee;font-size:13px;outline:none;
}
.driver-list { max-height:220px;overflow-y:auto; }
.driver-option {
  width:100%;display:block;padding:8px 12px;text-align:left;
  font-size:14px;border:none;background:none;cursor:pointer;
}
.driver-option:hover { background:#f5f5f5; }
.driver-option.selected { background:#e3f2fd;color:#1565c0;font-weight:500; }
.driver-empty { font-size:12px;color:#bbb;padding:10px 12px;margin:0; }

.routing-row { display:flex;align-items:center;gap:8px;flex-wrap:wrap; }
.routing-info { font-size:13px;color:#444;display:flex;align-items:center;gap:5px;flex:1; }
.routing-info--muted { color:#aaa; }
.routing-manual-badge { font-size:11px;background:#fff3e0;color:#e65100;padding:1px 6px;border-radius:4px; }
</style>
