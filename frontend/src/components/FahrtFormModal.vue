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

        <!-- Aufträge -->
        <section class="section">
          <h4>Aufträge</h4>

          <!-- Ausgewählte Aufträge (sortierbar) -->
          <div v-if="form.order_ids.length > 0" class="selected-orders">
            <div v-for="(orderId, idx) in form.order_ids" :key="orderId" class="selected-order">
              <div class="reorder-btns">
                <button type="button" :disabled="idx === 0" @click="moveOrder(idx, -1)">▲</button>
                <button type="button" :disabled="idx === form.order_ids.length - 1" @click="moveOrder(idx, 1)">▼</button>
              </div>
              <span class="order-num">{{ idx + 1 }}</span>
              <span class="order-check__label">
                <strong>{{ getOrder(orderId)?.destination }}</strong>
                <small>{{ formatTime(getOrder(orderId)?.deadline) }} · {{ getOrder(orderId)?.trip_type }}</small>
                <small v-if="getOrder(orderId)?.patient_name">
                  👤 {{ getOrder(orderId).patient_name }}<span v-if="getOrder(orderId).companion"> +1</span>
                </small>
              </span>
              <button type="button" class="btn-icon btn-remove" title="Entfernen" @click="removeOrder(orderId)">✕</button>
            </div>
          </div>

          <!-- Verfügbare Aufträge zum Hinzufügen -->
          <div v-if="availableOrders.length > 0" class="available-orders">
            <p class="available-label">Hinzufügen:</p>
            <div
              v-for="o in availableOrders"
              :key="o.id"
              class="available-order"
              @click="addOrder(o.id)"
            >
              <span class="available-order__plus">+</span>
              <span class="order-check__label">
                <strong>{{ o.destination }}</strong>
                <small>{{ formatTime(o.deadline) }} · {{ o.trip_type }}</small>
                <small v-if="o.patient_name">👤 {{ o.patient_name }}<span v-if="o.companion"> +1</span></small>
              </span>
            </div>
          </div>
          <p v-if="selectableOrders.length === 0" style="color:#aaa;font-size:13px">Keine offenen Aufträge</p>
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
import { computed, onMounted, reactive, ref } from 'vue'
import { useTripsStore } from '@/stores/trips'
import { useVehiclesStore } from '@/stores/vehicles'
import { api } from '@/api/client'

const props = defineProps({ trip: Object, openOrders: Array, preSelectedOrderId: String })
const emit = defineEmits(['saved', 'close'])

const selectableOrders = computed(() => {
  if (!props.trip) return props.openOrders
  const tripOrderIds = new Set(props.trip.orders.map((to) => to.order.id))
  const tripOrders = props.trip.orders.map((to) => to.order)
  const additionalOpen = props.openOrders.filter((o) => !tripOrderIds.has(o.id))
  return [...tripOrders, ...additionalOpen]
})

const tripsStore = useTripsStore()
const vehiclesStore = useVehiclesStore()
const users = ref([])
const saving = ref(false)
const error = ref(null)

const initialOrderIds = props.trip?.orders.map((to) => to.order.id) ?? []
if (props.preSelectedOrderId && !initialOrderIds.includes(props.preSelectedOrderId)) {
  initialOrderIds.push(props.preSelectedOrderId)
}

const form = reactive({
  name: props.trip?.name ?? '',
  driver_id: props.trip?.driver?.id ?? null,
  vehicle_id: props.trip?.vehicle?.id ?? null,
  order_ids: initialOrderIds,
  notes: props.trip?.notes ?? '',
})

const selectedOrders = computed(() =>
  selectableOrders.value.filter((o) => form.order_ids.includes(o.id))
)

const availableOrders = computed(() =>
  selectableOrders.value.filter((o) => !form.order_ids.includes(o.id))
)

function getOrder(orderId) {
  return selectableOrders.value.find((o) => o.id === orderId)
}

function addOrder(orderId) {
  if (!form.order_ids.includes(orderId)) form.order_ids.push(orderId)
}

function removeOrder(orderId) {
  const idx = form.order_ids.indexOf(orderId)
  if (idx !== -1) form.order_ids.splice(idx, 1)
}

function moveOrder(idx, delta) {
  const newIdx = idx + delta
  if (newIdx < 0 || newIdx >= form.order_ids.length) return
  const arr = [...form.order_ids]
  ;[arr[idx], arr[newIdx]] = [arr[newIdx], arr[idx]]
  form.order_ids.splice(0, form.order_ids.length, ...arr)
}

const usedSeats = computed(() => {
  let seats = 1
  for (const o of selectedOrders.value) {
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
const canSave = computed(() => form.order_ids.length > 0)

async function submit() {
  saving.value = true
  error.value = null
  try {
    const payload = {
      name: form.name || null,
      driver_id: form.driver_id,
      vehicle_id: form.vehicle_id,
      order_ids: form.order_ids,
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
.modal { background:#fff;border-radius:10px;width:560px;max-width:95vw;max-height:90vh;display:flex;flex-direction:column;box-shadow:0 8px 32px rgba(0,0,0,.2); }
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

.order-check__label { display:flex;flex-direction:column;gap:2px;flex:1; }
.order-check__label small { color:#888;font-size:11px; }

.selected-orders { display:flex;flex-direction:column;gap:4px;margin-bottom:10px; }
.selected-order {
  display:flex;align-items:center;gap:8px;
  padding:8px;border-radius:6px;border:1px solid #1565c0;background:#f0f7ff;
}
.reorder-btns { display:flex;flex-direction:column;gap:2px; }
.reorder-btns button {
  padding:0 4px;font-size:10px;line-height:1.4;border:1px solid #ccc;
  border-radius:3px;background:#fff;color:#555;cursor:pointer;
}
.reorder-btns button:disabled { opacity:0.3;cursor:default; }
.order-num {
  width:20px;height:20px;border-radius:50%;background:#1565c0;color:#fff;
  display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:600;flex-shrink:0;
}
.btn-remove {
  padding:2px 6px;font-size:12px;border-radius:4px;border:none;
  background:transparent;color:#aaa;cursor:pointer;flex-shrink:0;
}
.btn-remove:hover { color:#c62828; }

.available-label { font-size:11px;color:#aaa;margin-bottom:4px; }
.available-orders { display:flex;flex-direction:column;gap:4px; }
.available-order {
  display:flex;align-items:center;gap:8px;
  padding:8px;border-radius:6px;border:1px dashed #ddd;cursor:pointer;
}
.available-order:hover { border-color:#1565c0;background:#f8faff; }
.available-order__plus { font-size:16px;color:#1565c0;font-weight:600;flex-shrink:0;width:20px;text-align:center; }

.kapazitaet { display:flex;align-items:center;gap:10px;margin-bottom:6px; }
.kapazitaet__bar { flex:1;height:8px;background:#eee;border-radius:4px;overflow:hidden; }
.kapazitaet__fill { height:100%;background:#1565c0;border-radius:4px;transition:width .3s; }
.kapazitaet__fill.warn { background:#e65100; }
.kapazitaet__fill.over { background:#c62828; }
.over-text { color:#c62828;font-weight:600; }
.error { color:#c62828;font-size:13px;margin-top:4px; }
</style>
