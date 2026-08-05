<template>
  <div
    class="fahrt-karte"
    :class="{
      'fahrt-karte--drop-target': isDragOver && ['geplant', 'aktiv'].includes(trip.status),
      'fahrt-karte--konflikt': conflict,
      'fahrt-karte--beendet': ['abgeschlossen', 'abgebrochen'].includes(trip.status),
      'fahrt-karte--ueberfaellig': isUeberfaellig,
    }"
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
        <button v-if="['geplant', 'aktiv'].includes(trip.status)" class="btn-icon btn-icon--ghost" title="Fahrer-Ansicht öffnen (Vertretung)" @click="$emit('open-fahrer')">📱</button>
        <button v-if="trip.status === 'geplant'" class="btn-icon btn-icon--success" title="Fahrt starten" @click="onStart">▶</button>
        <button v-if="canComplete" class="btn-icon btn-icon--success" title="Fahrt abschließen" @click="onComplete">✓</button>
        <button v-if="canAbort" class="btn-icon btn-icon--ghost-muted" title="Fahrt abbrechen" @click="onAbort">✕</button>
        <button v-if="trip.status === 'geplant'" class="btn-icon btn-icon--ghost" title="Drucken" @click="$emit('print')">🖨</button>
        <button class="btn-icon btn-icon--ghost-muted" title="Änderungshistorie" @click="openHistory">🕘</button>
      </div>
    </div>

    <div v-if="conflict" class="fahrt-karte__konflikt-banner">
      ⚠ {{ conflict.reason }}
    </div>

    <div class="fahrt-karte__info">
      <span :class="{ 'info--warn': !trip.vehicle }">🚗 {{ trip.vehicle ? `${trip.vehicle.name} (${trip.vehicle.license_plate})` : 'Fahrzeug fehlt' }}</span>
      <span
        v-if="trip.driver"
        class="driver-link"
        title="Kontaktdaten anzeigen"
        @click="showContact = true"
      >👤 {{ trip.driver.name }}</span>
      <span v-else class="info--warn">👤 Fahrer fehlt</span>
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
      <span class="kapazitaet__label" title="Maximale gleichzeitige Belegung inkl. Fahrer">{{ usedSeats }} / {{ trip.vehicle.seats }} Sitze</span>
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
        <span class="stopp__deadline">{{ to.order.deadline ? formatTime(to.order.deadline) : '–' }}</span>
        <span :class="`badge badge--${to.order.trip_type}`" style="font-size:11px">{{ to.order.trip_type }}</span>
      </div>
    </VueDraggable>

    <!-- Fahrer-Kontaktdaten (Overlay) -->
    <Teleport to="body">
      <div v-if="showContact && trip.driver" class="overlay-backdrop" @click.self="showContact = false">
        <div class="overlay-card">
          <div class="overlay-card__header">
            <h3>👤 {{ trip.driver.name }}</h3>
            <button class="overlay-card__close" @click="showContact = false">✕</button>
          </div>
          <div class="overlay-card__body">
            <p v-if="trip.driver.phone">📞 <a :href="`tel:${trip.driver.phone}`">{{ trip.driver.phone }}</a></p>
            <p v-else class="overlay-muted">Keine Telefonnummer hinterlegt</p>
            <p v-if="trip.driver.email">✉️ <a :href="`mailto:${trip.driver.email}`">{{ trip.driver.email }}</a></p>
          </div>
        </div>
      </div>

      <!-- Änderungshistorie (Overlay) -->
      <div v-if="showHistory" class="overlay-backdrop" @click.self="showHistory = false">
        <div class="overlay-card">
          <div class="overlay-card__header">
            <h3>🕘 Änderungshistorie – {{ trip.name || 'Fahrt #' + trip.trip_number }}</h3>
            <button class="overlay-card__close" @click="showHistory = false">✕</button>
          </div>
          <div class="overlay-card__body">
            <p v-if="historyLoading" class="overlay-muted">Laden…</p>
            <p v-else-if="history.length === 0" class="overlay-muted">Keine Einträge</p>
            <div v-for="(h, i) in history" :key="i" class="history__entry">
              <span class="history__time">{{ formatTime(h.changed_at) }}</span>
              <span class="history__user">{{ h.changed_by_name }}</span>
              <span class="history__change">
                <template v-if="h.destination">Ziel „{{ h.destination }}" {{ h.new_status === 'erledigt' ? 'erledigt' : 'hinzugefügt' }}</template>
                <template v-else-if="h.old_status">{{ h.old_status }} → {{ h.new_status }}</template>
                <template v-else>angelegt ({{ h.new_status }})</template>
              </span>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { VueDraggable } from 'vue-draggable-plus'
import { useNow } from '@/composables/useNow'
import { api } from '@/api/client'
import { computeNeededSeats } from '@/utils/seatOccupancy'

const props = defineProps({ trip: Object, conflict: Object })
const now = useNow()
const emit = defineEmits(['start', 'complete', 'abort', 'print', 'edit', 'open-fahrer', 'drop-order', 'reorder', 'order-moved', 'stop-drag-start', 'stop-drag-end'])

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

function onStart() {
  if (!confirm(`"${props.trip.name || 'Fahrt #' + props.trip.trip_number}" starten?\n\nAlle Aufträge der Fahrt gelten dann als unterwegs, der Fahrer sieht die Fahrt als gestartet.`)) return
  emit('start')
}

function onComplete() {
  const openCount = props.trip.orders.filter((to) => to.order.status !== 'erledigt').length
  if (openCount > 0) {
    const confirmed = confirm(
      `${openCount} Auftrag${openCount === 1 ? ' ist' : 'e sind'} noch nicht erledigt.\n\nAlle Aufträge als erledigt markieren und die Fahrt abschließen?`
    )
    if (!confirmed) return
    emit('complete', true)
  } else {
    emit('complete', false)
  }
}

// Noch nicht gestartete Fahrt, deren geplante Startzeit bereits verstrichen ist
const isUeberfaellig = computed(() =>
  props.trip.status === 'geplant' &&
  props.trip.planned_start_time &&
  new Date(props.trip.planned_start_time).getTime() < now.value
)

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

// localOrders statt props.trip.orders, damit der Balken beim Umsortieren sofort reagiert
const usedSeats = computed(() =>
  computeNeededSeats(localOrders.value.map((to) => to.order))
)

const seatRatio = computed(() =>
  props.trip.vehicle ? usedSeats.value / props.trip.vehicle.seats : 0
)

const canComplete = computed(() => props.trip.status === 'aktiv')

const canAbort = computed(() =>
  ['geplant', 'aktiv'].includes(props.trip.status)
)

function formatTime(iso) {
  return new Date(iso).toLocaleString('de-DE', { dateStyle: 'short', timeStyle: 'short' })
}

const showContact = ref(false)
const showHistory = ref(false)
const historyLoading = ref(false)
const history = ref([])

// Historie bei jedem Öffnen frisch aus der DB laden
async function openHistory() {
  showHistory.value = true
  historyLoading.value = true
  try {
    history.value = await api.get(`/trips/${props.trip.id}/history`)
  } catch {
    history.value = []
  } finally {
    historyLoading.value = false
  }
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
.fahrt-karte--ueberfaellig {
  background: #fdf1f1;
  border-color: #f0c4c4;
}
.fahrt-karte--konflikt {
  border-color: #e53935;
  background: #fff8f8;
}
.fahrt-karte--beendet {
  opacity: 0.65;
}
.fahrt-karte__konflikt-banner {
  background: #ffebee;
  border: 1px solid #ef9a9a;
  border-radius: 4px;
  color: #c62828;
  font-size: 12px;
  font-weight: 500;
  padding: 5px 8px;
  margin-bottom: 8px;
  line-height: 1.4;
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

.driver-link { cursor: pointer; color: #1565c0; }
.driver-link:hover { text-decoration: underline; }

.overlay-backdrop {
  position: fixed; inset: 0;
  background: rgba(0,0,0,.45);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000;
}
.overlay-card {
  background: #fff;
  border-radius: 12px;
  width: 100%;
  max-width: 440px;
  max-height: 80vh;
  display: flex; flex-direction: column;
  box-shadow: 0 8px 32px rgba(0,0,0,.18);
}
.overlay-card__header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px 12px;
  border-bottom: 1px solid #eee;
}
.overlay-card__header h3 { font-size: 15px; font-weight: 600; margin: 0; }
.overlay-card__close {
  background: none; border: none;
  font-size: 16px; color: #888; cursor: pointer;
  padding: 2px 6px; border-radius: 4px; line-height: 1;
}
.overlay-card__close:hover { background: #f0f0f0; color: #333; }
.overlay-card__body {
  padding: 16px 20px;
  overflow-y: auto;
  display: flex; flex-direction: column; gap: 6px;
  font-size: 14px;
}
.overlay-card__body a { color: #1565c0; text-decoration: none; }
.overlay-muted { color: #aaa; font-size: 13px; }

.history__entry { display: flex; gap: 10px; font-size: 13px; color: #555; }
.history__time { color: #888; white-space: nowrap; }
.history__user { font-weight: 600; white-space: nowrap; }
.history__change { flex: 1; }
</style>
