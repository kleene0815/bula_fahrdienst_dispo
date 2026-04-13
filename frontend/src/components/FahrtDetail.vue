<template>
  <div class="fahrt-detail">
    <!-- Kopf -->
    <div class="detail-header">
      <div>
        <h2>{{ trip.name || 'Fahrt #' + trip.trip_number }}</h2>
        <span :class="`badge badge--${trip.status}`">{{ trip.status }}</span>
      </div>
      <div class="detail-header__vehicle">
        🚗 {{ trip.vehicle?.name }} ({{ trip.vehicle?.license_plate }})
      </div>
    </div>

    <!-- Bestätigungsmeldung nach Abschluss -->
    <div v-if="completed" class="success-banner">
      ✓ Fahrt abgeschlossen — {{ trip.vehicle?.name }} und du bist wieder frei.
    </div>

    <!-- Fahrt starten -->
    <div v-if="trip.status === 'geplant'" class="action-bar">
      <button class="btn-success" style="width:100%" @click="$emit('start')">
        Fahrt starten
      </button>
    </div>

    <!-- Stoppliste -->
    <ol class="stopps">
      <li
        v-for="to in trip.orders"
        :key="to.order.id"
        class="stopp-item"
        :class="{ 'stopp-item--done': to.order.status === 'erledigt', 'stopp-item--active': isActiveStop(to) }"
      >
        <!-- Verbindungslinie -->
        <div class="stopp-item__line"></div>

        <!-- Kreis -->
        <div class="stopp-item__circle">
          <span v-if="to.order.status === 'erledigt'">✓</span>
          <span v-else>{{ to.sort_order }}</span>
        </div>

        <!-- Inhalt -->
        <div class="stopp-item__content">
          <div class="stopp-item__header" @click="toggleExpand(to.order.id)">
            <span class="stopp-item__ziel" :class="{ done: to.order.status === 'erledigt' }">
              {{ to.order.destination }}
            </span>
            <span class="stopp-item__time">{{ formatTime(to.order.deadline) }}</span>
            <span :class="`badge badge--${to.order.trip_type}`" style="font-size:11px">{{ to.order.trip_type }}</span>
            <span class="stopp-item__expand">{{ expanded.has(to.order.id) ? '▲' : '▼' }}</span>
          </div>

          <!-- Detailansicht (aufklappbar) -->
          <div v-if="expanded.has(to.order.id)" class="stopp-item__details">
            <p v-if="to.order.destination_street || to.order.destination_city" class="detail-row">
              📍 {{ [to.order.destination_street, to.order.destination_city].filter(Boolean).join(', ') }}
            </p>
            <template v-if="to.order.patient_name">
              <p class="detail-row">👤 {{ to.order.patient_name }}<span v-if="to.order.companion"> + Begleitperson</span></p>
              <p v-if="to.order.phone" class="detail-row">
                📞 <a :href="`tel:${to.order.phone}`">{{ to.order.phone }}</a>
              </p>
              <p v-if="to.order.requester_station" class="detail-row">📋 {{ to.order.requester_station }}</p>
            </template>
            <p v-if="to.order.notes" class="detail-row detail-row--notes">{{ to.order.notes }}</p>
          </div>

          <!-- Stopp erledigen -->
          <button
            v-if="trip.status === 'aktiv' && to.order.status === 'unterwegs'"
            class="btn-primary stopp-item__done-btn"
            @click="$emit('complete-stop', to.order.id)"
          >
            Stopp erledigt ✓
          </button>
        </div>
      </li>

      <!-- Rückfahrt-Element -->
      <li v-if="allStopsDone && trip.status === 'aktiv'" class="stopp-item stopp-item--rueckfahrt">
        <div class="stopp-item__circle stopp-item__circle--home">🏕</div>
        <div class="stopp-item__content">
          <strong>Rückfahrt zum Lager</strong>
          <button class="btn-success" style="margin-top:10px;width:100%" @click="$emit('complete')">
            Fahrt abschließen ✓
          </button>
        </div>
      </li>
    </ol>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'

const props = defineProps({ trip: Object })
defineEmits(['start', 'complete-stop', 'complete'])

const expanded = reactive(new Set())
const completed = ref(false)

const allStopsDone = computed(() =>
  props.trip.orders.every((to) => to.order.status === 'erledigt')
)

function isActiveStop(to) {
  if (props.trip.status !== 'aktiv') return false
  return to.order.status === 'unterwegs'
}

function toggleExpand(id) {
  if (expanded.has(id)) expanded.delete(id)
  else expanded.add(id)
}

function formatTime(iso) {
  return new Date(iso).toLocaleString('de-DE', { dateStyle: 'short', timeStyle: 'short' })
}
</script>

<style scoped>
.fahrt-detail { max-width: 560px; margin: 0 auto; }

.detail-header {
  background: #fff;
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 1px 3px rgba(0,0,0,.08);
}
.detail-header h2 { font-size: 18px; margin-bottom: 4px; }
.detail-header__vehicle { font-size: 13px; color: #666; }

.success-banner {
  background: #e8f5e9;
  color: #2e7d32;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 12px;
  font-weight: 500;
}

.action-bar { margin-bottom: 16px; }

.stopps { list-style: none; position: relative; }

.stopp-item {
  display: flex;
  gap: 12px;
  padding-bottom: 16px;
  position: relative;
}
.stopp-item__line {
  position: absolute;
  left: 19px;
  top: 28px;
  bottom: 0;
  width: 2px;
  background: #e0e0e0;
}
.stopp-item:last-child .stopp-item__line { display: none; }

.stopp-item__circle {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: #e0e0e0;
  color: #555;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 15px;
  flex-shrink: 0;
  z-index: 1;
}
.stopp-item--done .stopp-item__circle { background: #2e7d32; color: #fff; }
.stopp-item--active .stopp-item__circle { background: #e65100; color: #fff; }
.stopp-item__circle--home { background: #1565c0; color: #fff; font-size: 18px; }

.stopp-item__content { flex: 1; background: #fff; border-radius: 8px; padding: 10px 12px; box-shadow: 0 1px 3px rgba(0,0,0,.06); }
.stopp-item__header { display: flex; align-items: center; gap: 8px; cursor: pointer; }
.stopp-item__ziel { flex: 1; font-weight: 600; }
.stopp-item__ziel.done { text-decoration: line-through; color: #aaa; }
.stopp-item__time { font-size: 12px; color: #888; }
.stopp-item__expand { font-size: 10px; color: #bbb; }

.stopp-item__details { margin-top: 8px; padding-top: 8px; border-top: 1px solid #eee; }
.detail-row { font-size: 13px; color: #555; margin-bottom: 4px; }
.detail-row a { color: #1565c0; text-decoration: none; }
.detail-row--notes { color: #888; font-style: italic; }

.stopp-item__done-btn { margin-top: 10px; width: 100%; }

.stopp-item--rueckfahrt .stopp-item__content { text-align: center; }
</style>
