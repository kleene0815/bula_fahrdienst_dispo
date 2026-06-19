<template>
  <div
    class="fahrt-karte"
    :class="{ 'fahrt-karte--drop-target': isDragOver && ['geplant', 'aktiv'].includes(trip.status) }"
    @dragover.prevent="isDragOver = ['geplant', 'aktiv'].includes(trip.status)"
    @dragleave="isDragOver = false"
    @drop="onDrop"
  >
    <div class="fahrt-karte__header">
      <div class="fahrt-karte__title">
        <strong>{{ trip.name || 'Fahrt #' + trip.trip_number }}</strong>
        <span :class="`badge badge--${trip.status}`">{{ trip.status }}</span>
        <span v-if="routeCities.length" class="fahrt-karte__route">{{ routeCities.join(' · ') }}</span>
      </div>
      <div class="fahrt-karte__actions">
        <button v-if="trip.status === 'geplant'" class="btn-icon btn-icon--ghost" title="Bearbeiten" @click="$emit('edit')">✏</button>
        <button v-if="canComplete" class="btn-icon btn-icon--success" title="Fahrt abschließen" @click="$emit('complete')">✓</button>
        <button v-if="canAbort" class="btn-icon btn-icon--ghost-muted" title="Fahrt abbrechen" @click="onAbort">✕</button>
        <button v-if="trip.status === 'geplant'" class="btn-icon btn-icon--ghost" title="Drucken" @click="$emit('print')">🖨</button>
      </div>
    </div>

    <div class="fahrt-karte__info">
      <span :class="{ 'info--warn': !trip.vehicle }">🚗 {{ trip.vehicle ? `${trip.vehicle.name} (${trip.vehicle.license_plate})` : 'Fahrzeug fehlt' }}</span>
      <span :class="{ 'info--warn': !trip.driver }">👤 {{ trip.driver?.name ?? 'Fahrer fehlt' }}</span>
    </div>

    <!-- Routing-Info (nur für geplante Fahrten) -->
    <div v-if="trip.status === 'geplant'" class="fahrt-karte__routing">
      <template v-if="trip.planned_start_time">
        <span class="routing-start">
          🕐 <strong>{{ formatTime(trip.planned_start_time) }}</strong>
          <span v-if="trip.start_time_manual_override" class="routing-badge routing-badge--manual" title="Manuell gesetzt">✋</span>
        </span>
        <template v-if="trip.estimated_duration_minutes">
          <span class="routing-duration">{{ trip.estimated_duration_minutes }} min</span>
          <span class="routing-end">🏁 <strong>{{ formatEndTime(trip.planned_start_time, trip.estimated_duration_minutes) }}</strong></span>
        </template>
      </template>
      <span v-else class="routing-badge routing-badge--pending">Startzeit unbekannt</span>
    </div>

    <!-- Kapazitätsindikator -->
    <div v-if="trip.status !== 'abgeschlossen' && trip.vehicle" class="kapazitaet">
      <div class="kapazitaet__bar">
        <div
          class="kapazitaet__fill"
          :class="{ 'kapazitaet__fill--warn': seatRatio > 0.7, 'kapazitaet__fill--over': seatRatio > 1 }"
          :style="{ width: Math.min(seatRatio * 100, 100) + '%' }"
        ></div>
      </div>
      <span class="kapazitaet__label">{{ usedSeats }} / {{ trip.vehicle.seats }} Sitze</span>
    </div>

    <!-- Stoppliste -->
    <VueDraggable
      v-model="localOrders"
      :group="{ name: 'trip-stops', pull: trip.status === 'geplant', put: trip.status === 'geplant' }"
      :disabled="trip.status !== 'geplant'"
      :animation="150"
      handle=".drag-handle"
      class="stopps"
      :data-trip-id="trip.id"
      @start="onStopDragStart"
      @end="onStopReorder"
      @add="onStopAdded"
    >
      <div v-for="(to, index) in localOrders" :key="to.order.id" class="stopp" :class="`stopp--${to.order.status}`">
        <span v-if="trip.status === 'geplant'" class="drag-handle">⠿</span>
        <span class="stopp__num">{{ index + 1 }}</span>
        <span class="stopp__ziel">{{ to.order.destination }}</span>
        <span class="stopp__deadline">{{ formatTime(to.order.deadline) }}</span>
        <span :class="`badge badge--${to.order.trip_type}`" style="font-size:11px">{{ to.order.trip_type }}</span>
      </div>
    </VueDraggable>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { VueDraggable } from 'vue-draggable-plus'

const props = defineProps({ trip: Object })
const emit = defineEmits(['complete', 'abort', 'print', 'edit', 'drop-order', 'reorder', 'order-moved', 'stop-drag-start', 'stop-drag-end'])

const isDragOver = ref(false)

// Lokale Kopie für VueDraggable (wird bei Store-Updates synchronisiert)
const localOrders = ref([...props.trip.orders])
watch(() => props.trip.orders, (newOrders) => {
  localOrders.value = [...newOrders]
}, { deep: true })

function onStopDragStart(evt) {
  const to = localOrders.value[evt.oldIndex]
  if (!to) return
  // Drag-Infos über Vue-Event weitergeben (zuverlässiger als dataTransfer bei SortableJS)
  emit('stop-drag-start', { orderId: to.order.id, sourceTripId: props.trip.id })
}

function onStopReorder(evt) {
  emit('stop-drag-end')
  if (evt.from !== evt.to) return  // cross-trip move — wird von @add behandelt
  if (evt.oldIndex === evt.newIndex) return
  emit('reorder', localOrders.value.map((to) => to.order.id))
}

function onStopAdded(evt) {
  const movedOrder = localOrders.value[evt.newIndex]
  if (!movedOrder) return
  const sourceTripId = evt.from.dataset.tripId
  emit('order-moved', {
    orderId: movedOrder.order.id,
    sourceTripId,
    newOrderIds: localOrders.value.map((to) => to.order.id),
  })
}

function onDrop(event) {
  isDragOver.value = false
  if (!['geplant', 'aktiv'].includes(props.trip.status)) return
  const orderId = event.dataTransfer.getData('order-id')
  if (!orderId) return
  const sourceTripId = event.dataTransfer.getData('source-trip-id')
  if (sourceTripId === props.trip.id) return // Innerhalb derselben Fahrt — von VueDraggable behandelt
  emit('drop-order', { orderId, sourceTripId: sourceTripId || null, tripStatus: props.trip.status })
}

function onAbort() {
  if (!confirm('Fahrt wirklich abbrechen?')) return
  emit('abort')
}

const routeCities = computed(() => {
  const seen = new Set()
  const cities = []
  for (const { order: o } of props.trip.orders) {
    const city = o.destination_city?.replace(/^\d{5}\s+/, '').trim()
    if (city && !seen.has(city)) {
      seen.add(city)
      cities.push(city)
    }
  }
  return cities
})

const usedSeats = computed(() => {
  let seats = 1 // Fahrer
  for (const { order: o } of props.trip.orders) {
    if (o.patient_name) {
      seats += 1
      if (o.companion) seats += 1
    }
  }
  return seats
})

const seatRatio = computed(() =>
  props.trip.vehicle ? usedSeats.value / props.trip.vehicle.seats : 0
)

const canComplete = computed(() =>
  props.trip.status === 'aktiv' &&
  props.trip.orders.every((to) => to.order.status === 'erledigt')
)

const canAbort = computed(() =>
  ['geplant', 'aktiv'].includes(props.trip.status)
)

function formatTime(iso) {
  return new Date(iso).toLocaleString('de-DE', { dateStyle: 'short', timeStyle: 'short' })
}

function formatEndTime(startIso, durationMinutes) {
  const end = new Date(new Date(startIso).getTime() + durationMinutes * 60_000)
  return end.toLocaleString('de-DE', { dateStyle: 'short', timeStyle: 'short' })
}
</script>

<style scoped>
.fahrt-karte {
  background: #fff;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
  padding: 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,.06);
  transition: border-color .15s, box-shadow .15s;
}
.fahrt-karte--drop-target {
  border-color: #1565c0;
  box-shadow: 0 0 0 2px rgba(21,101,192,.25);
}
.fahrt-karte__header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 6px; gap: 8px; }
.fahrt-karte__title { display: flex; align-items: center; gap: 8px; min-width: 0; }
.fahrt-karte__route { color: #555; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; min-width: 0; flex: 1; }
.fahrt-karte__actions { display: flex; gap: 4px; flex-wrap: wrap; }
.fahrt-karte__info { font-size: 12px; color: #666; display: flex; gap: 16px; margin-bottom: 8px; }

.info--warn { color: #e65100; font-weight: 500; }

.kapazitaet { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.kapazitaet__bar { flex: 1; height: 6px; background: #eee; border-radius: 3px; overflow: hidden; }
.kapazitaet__fill { height: 100%; background: #1565c0; border-radius: 3px; transition: width .3s; }
.kapazitaet__fill--warn { background: #e65100; }
.kapazitaet__fill--over { background: #c62828; }
.kapazitaet__label { font-size: 11px; color: #666; white-space: nowrap; }

.stopps { list-style: none; display: flex; flex-direction: column; gap: 4px; }
.stopp {
  display: flex; align-items: center; gap: 8px;
  font-size: 12px; padding: 4px 6px; border-radius: 4px;
  background: #f9f9f9;
}
.stopp--erledigt { opacity: 0.5; text-decoration: line-through; }
.stopp__num { width: 20px; height: 20px; border-radius: 50%; background: #e0e0e0; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 600; flex-shrink: 0; }
.stopp__ziel { flex: 1; }
.stopp__deadline { color: #888; }
.drag-handle { color: #ccc; cursor: grab; font-size: 14px; flex-shrink: 0; line-height: 1; }
.drag-handle:hover { color: #999; }
.drag-handle:active { cursor: grabbing; }

.btn-icon {
  padding: 4px 8px;
  font-size: 13px;
  border-radius: 4px;
  line-height: 1;
  border: none;
}
.btn-icon--ghost {
  background: transparent;
  color: #1565c0;
  border: 1px solid #1565c0;
}
.btn-icon--success {
  background: #2e7d32;
  color: #fff;
}
.btn-icon--ghost-muted {
  background: transparent;
  color: #aaa;
  border: 1px solid #ddd;
}
.btn-icon--ghost-muted:hover {
  color: #c62828;
  border-color: #c62828;
}

.fahrt-karte__routing {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 12px;
  background: #f5f8ff;
  border-top: 1px solid #e8eef8;
  font-size: 12px;
  color: #555;
}
.routing-start { display: flex; align-items: center; gap: 5px; }
.routing-duration { color: #888; }
.routing-badge {
  font-size: 11px;
  padding: 1px 7px;
  border-radius: 4px;
  font-weight: 500;
}
.routing-badge--manual { background: #fff3e0; color: #e65100; }
.routing-badge--pending { background: #f5f5f5; color: #aaa; }
</style>
