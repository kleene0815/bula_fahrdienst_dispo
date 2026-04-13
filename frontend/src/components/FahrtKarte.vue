<template>
  <div
    class="fahrt-karte"
    :class="{ 'fahrt-karte--drop-target': isDragOver && trip.status === 'geplant' }"
    @dragover.prevent="isDragOver = trip.status === 'geplant'"
    @dragleave="isDragOver = false"
    @drop="onDrop"
  >
    <div class="fahrt-karte__header">
      <div class="fahrt-karte__title">
        <strong>Fahrt #{{ trip.trip_number }}</strong>
        <span :class="`badge badge--${trip.status}`">{{ trip.status }}</span>
      </div>
      <div class="fahrt-karte__actions">
        <button v-if="trip.status === 'geplant'" class="btn-ghost" style="font-size:12px;padding:4px 8px" @click="$emit('edit')">Bearbeiten</button>
        <button v-if="canComplete" class="btn-success" style="font-size:12px;padding:4px 8px" @click="$emit('complete')">Fahrt abschließen</button>
        <button v-if="canAbort" class="btn-danger" style="font-size:12px;padding:4px 8px" @click="$emit('abort')">Abbrechen</button>
        <button v-if="trip.status === 'geplant'" class="btn-ghost" style="font-size:12px;padding:4px 8px" @click="$emit('print')">Drucken</button>
      </div>
    </div>

    <div class="fahrt-karte__info">
      <span>🚗 {{ trip.vehicle?.name }} ({{ trip.vehicle?.license_plate }})</span>
      <span>👤 {{ trip.driver?.name }}</span>
    </div>

    <!-- Kapazitätsindikator -->
    <div v-if="trip.status !== 'abgeschlossen'" class="kapazitaet">
      <div class="kapazitaet__bar">
        <div
          class="kapazitaet__fill"
          :class="{ 'kapazitaet__fill--warn': seatRatio > 0.7, 'kapazitaet__fill--over': seatRatio > 1 }"
          :style="{ width: Math.min(seatRatio * 100, 100) + '%' }"
        ></div>
      </div>
      <span class="kapazitaet__label">{{ usedSeats }} / {{ trip.vehicle?.seats ?? '?' }} Sitze</span>
    </div>

    <!-- Stoppliste -->
    <ol class="stopps">
      <li v-for="to in trip.orders" :key="to.order.id" class="stopp" :class="`stopp--${to.order.status}`">
        <span class="stopp__num">{{ to.sort_order }}</span>
        <span class="stopp__ziel">{{ to.order.destination }}</span>
        <span class="stopp__deadline">{{ formatTime(to.order.deadline) }}</span>
        <span :class="`badge badge--${to.order.trip_type}`" style="font-size:11px">{{ to.order.trip_type }}</span>
      </li>
    </ol>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({ trip: Object })
const emit = defineEmits(['complete', 'abort', 'print', 'edit', 'drop-order'])

const isDragOver = ref(false)

function onDrop(event) {
  isDragOver.value = false
  if (props.trip.status !== 'geplant') return
  const orderId = event.dataTransfer.getData('order-id')
  if (!orderId) return
  emit('drop-order', orderId)
}

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
.fahrt-karte__title { display: flex; align-items: center; gap: 8px; }
.fahrt-karte__actions { display: flex; gap: 6px; flex-wrap: wrap; }
.fahrt-karte__info { font-size: 12px; color: #666; display: flex; gap: 16px; margin-bottom: 8px; }

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
</style>
