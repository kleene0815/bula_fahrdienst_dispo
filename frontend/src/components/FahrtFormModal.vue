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
          <div class="card-grid">
            <button
              v-for="u in users"
              :key="u.id"
              class="select-card"
              :class="{ selected: form.driver_id === u.id }"
              type="button"
              @click="form.driver_id = form.driver_id === u.id ? null : u.id"
            >{{ u.name }}</button>
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
                handle=".drag-handle"
                class="drop-zone drop-zone--selected"
              >
                <div
                  v-for="(o, idx) in selectedOrderObjects"
                  :key="o.id"
                  class="order-item order-item--selected"
                >
                  <span class="drag-handle" title="Ziehen zum Sortieren oder Entfernen">⠿</span>
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
                handle=".drag-handle"
                :sort="false"
                class="drop-zone"
              >
                <div
                  v-for="o in availableOrderObjects"
                  :key="o.id"
                  class="order-item"
                >
                  <span class="drag-handle" title="In Fahrt ziehen">⠿</span>
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
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { VueDraggable } from 'vue-draggable-plus'
import { useTripsStore } from '@/stores/trips'
import { useVehiclesStore } from '@/stores/vehicles'
import { api } from '@/api/client'

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
const saving = ref(false)
const error = ref(null)

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

// Kapazitätsberechnung basiert auf ausgewählten Aufträgen
const usedSeats = computed(() => {
  let seats = 1
  for (const o of selectedOrderObjects.value) {
    if (o.patient_name) {
      seats += 1
      if (o.companion) seats += 1
    }
  }
  return seats
})

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
  if (!iso) return ''
  return new Date(iso).toLocaleString('de-DE', { dateStyle: 'short', timeStyle: 'short' })
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
  user-select:none;
}
.order-item--selected { background:#f0f7ff;border-color:#c5d9f1; }

.drag-handle {
  cursor:grab;color:#ccc;font-size:15px;flex-shrink:0;padding-top:1px;
  line-height:1;
}
.drag-handle:hover { color:#888; }
.drag-handle:active { cursor:grabbing; }

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
</style>
