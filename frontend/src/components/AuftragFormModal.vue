<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal">
      <div class="modal__header">
        <h3>
          {{ readonly ? 'Auftragsdetails' : (order ? 'Auftrag bearbeiten' : 'Neuer Auftrag') }}
          <span v-if="readonly && order" :class="`badge badge--${order.status}`" style="margin-left:8px">{{ statusLabel }}</span>
        </h3>
        <button class="btn-ghost" @click="$emit('close')">✕</button>
      </div>
      <form class="modal__body" @submit.prevent="submit">
        <fieldset :disabled="readonly" class="fields">
        <div class="field">
          <label>Auftraggeber / Station</label>
          <input v-model="form.requester_station" type="text" placeholder="z.B. Sanistation Nord" />
        </div>
        <div class="field">
          <label>Auftragstyp *</label>
          <select v-model="form.trip_type" required>
            <option value="besorgung">Besorgung</option>
            <option value="hinfahrt">Hinfahrt</option>
            <option value="abholung">Abholung</option>
          </select>
        </div>
        <div class="field">
          <label>Zieltyp *</label>
          <select v-model="form.destination_type" required>
            <option value="apotheke">Apotheke</option>
            <option value="arzt">Arzt</option>
            <option value="krankenhaus">Krankenhaus</option>
            <option value="sonstiges">Sonstiges</option>
          </select>
        </div>
        <div class="field">
          <label>Name / Bezeichnung des Ziels *</label>
          <div class="autocomplete-wrap">
            <input
              v-model="form.destination"
              type="text"
              required
              placeholder="z.B. Apotheke am Markt"
              autocomplete="off"
              @input="onDestinationInput"
              @keydown.down.prevent="acIndex = Math.min(acIndex + 1, acFiltered.length - 1)"
              @keydown.up.prevent="acIndex = Math.max(acIndex - 1, 0)"
              @keydown.enter.prevent="acIndex >= 0 && selectSuggestion(acFiltered[acIndex])"
              @keydown.escape="acOpen = false"
              @blur="onDestinationBlur"
            />
            <ul v-if="acOpen && acFiltered.length" class="autocomplete-list">
              <li
                v-for="(s, i) in acFiltered"
                :key="i"
                :class="{ 'autocomplete-list__item--active': i === acIndex }"
                @mousedown.prevent="selectSuggestion(s)"
              >
                <span class="ac-name">{{ s.name }}</span>
                <span class="ac-addr">{{ s.street }}, {{ s.city }}</span>
              </li>
            </ul>
          </div>
        </div>
        <div class="field">
          <label>Straße / Hausnummer</label>
          <input v-model="form.destination_street" type="text" placeholder="z.B. Hauptstraße 12" />
        </div>
        <div class="field">
          <label>PLZ / Ort</label>
          <input v-model="form.destination_city" type="text" placeholder="z.B. 86150 Augsburg" />
        </div>
        <div class="field">
          <label>Deadline / Termin {{ readonly ? '' : '*' }}</label>
          <p v-if="readonly" class="deadline-static">
            {{ order?.deadline ? formatDeadline(order.deadline) : 'Noch keine Deadline (erwartete Rückfahrt)' }}
          </p>
          <div v-else class="deadline-row">
            <div class="deadline-date-btns">
              <button
                type="button"
                :class="['btn-date', deadlineDateMode === 'heute' && 'btn-date--active']"
                @click="deadlineDateMode = 'heute'"
              >Heute</button>
              <button
                type="button"
                :class="['btn-date', deadlineDateMode === 'morgen' && 'btn-date--active']"
                @click="deadlineDateMode = 'morgen'"
              >Morgen</button>
              <button
                type="button"
                :class="['btn-date', deadlineDateMode === 'datum' && 'btn-date--active']"
                @click="deadlineDateMode = 'datum'"
              >Datum wählen</button>
            </div>
            <input
              v-if="deadlineDateMode === 'datum'"
              v-model="deadlineDate"
              type="date"
              :required="!readonly"
              class="deadline-date-input"
            />
            <input
              v-model="deadlineTime"
              type="time"
              :required="!readonly"
              class="deadline-time-input"
            />
          </div>
        </div>
        <div class="field">
          <label>Priorität *</label>
          <select v-model="form.priority" required>
            <option value="gering">Gering</option>
            <option value="normal">Normal</option>
            <option value="hoch">Hoch</option>
          </select>
        </div>

        <!-- Patientenfelder nur bei hinfahrt/abholung -->
        <template v-if="form.trip_type !== 'besorgung'">
          <div class="field">
            <label>Patientenname</label>
            <input v-model="form.patient_name" type="text" />
          </div>
          <div class="field">
            <label>Telefonnummer</label>
            <input v-model="form.phone" type="tel" />
          </div>
          <div class="field field--toggle">
            <label>
              <input v-model="form.companion" type="checkbox" />
              Begleitperson fährt mit
            </label>
          </div>
        </template>

        <div v-if="form.trip_type === 'hinfahrt'" class="field field--toggle">
          <label>
            <input v-model="form.create_return_order" type="checkbox" />
            Rückfahrt vormerken (Abholung wird nach Erledigung automatisch angelegt)
          </label>
        </div>

        <div class="field">
          <label>Bemerkungen für den Fahrer</label>
          <textarea v-model="form.notes" rows="3"></textarea>
        </div>

        </fieldset>

        <!-- Änderungshistorie (nur für bestehende Aufträge) -->
        <div v-if="order" class="history">
          <button type="button" class="history__toggle" @click="toggleHistory">
            🕘 Änderungshistorie {{ showHistory ? '▲' : '▼' }}
          </button>
          <div v-if="showHistory" class="history__list">
            <p v-if="historyLoading" class="history__empty">Laden…</p>
            <p v-else-if="history.length === 0" class="history__empty">Keine Einträge</p>
            <div v-for="(h, i) in history" :key="i" class="history__entry">
              <span class="history__time">{{ formatDeadline(h.changed_at) }}</span>
              <span class="history__user">{{ h.changed_by_name }}</span>
              <span class="history__change">
                <template v-if="h.old_status">{{ statusText(h.old_status) }} → {{ statusText(h.new_status) }}</template>
                <template v-else>angelegt ({{ statusText(h.new_status) }})</template>
              </span>
            </div>
          </div>
        </div>

        <p v-if="error" class="error">{{ error }}</p>
        <div class="modal__footer">
          <button type="button" class="btn-ghost" @click="$emit('close')">{{ readonly ? 'Schließen' : 'Abbrechen' }}</button>
          <button v-if="!readonly" type="submit" class="btn-primary" :disabled="saving">
            {{ saving ? 'Wird gespeichert…' : 'Speichern' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch, onMounted } from 'vue'
import { useOrdersStore } from '@/stores/orders'
import { api } from '@/api/client'

const props = defineProps({ order: Object, readonly: Boolean })
const emit = defineEmits(['saved', 'close'])

const statusLabel = computed(() =>
  props.order?.status === 'erwartete_rueckfahrt' ? 'erwartete Rückfahrt' : props.order?.status
)
const ordersStore = useOrdersStore()
const saving = ref(false)
const error = ref(null)

const suggestions = ref([])
const acOpen = ref(false)
const acIndex = ref(-1)

const acFiltered = computed(() => {
  const q = form.destination.toLowerCase()
  if (!q) return suggestions.value
  return suggestions.value.filter((s) => s.name.toLowerCase().includes(q))
})

function onDestinationInput() {
  acOpen.value = true
  acIndex.value = -1
}

function onDestinationBlur() {
  setTimeout(() => { acOpen.value = false }, 150)
}

function selectSuggestion(s) {
  form.destination = s.name
  form.destination_street = s.street
  form.destination_city = s.city
  acOpen.value = false
  acIndex.value = -1
}

const deadlineDateMode = ref('heute')
const deadlineDate = ref(today())
const deadlineTime = ref('17:00')

const form = reactive({
  trip_type: 'besorgung',
  destination_type: 'apotheke',
  destination: '',
  destination_street: '',
  destination_city: '',
  priority: 'normal',
  patient_name: '',
  phone: '',
  companion: false,
  create_return_order: true,
  notes: '',
  requester_station: '',
})

function today() {
  const d = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`
}

function tomorrow() {
  const d = new Date()
  d.setDate(d.getDate() + 1)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`
}

function resolvedDeadlineDate() {
  if (deadlineDateMode.value === 'heute') return today()
  if (deadlineDateMode.value === 'morgen') return tomorrow()
  return deadlineDate.value
}

// Beim Bearbeiten: Formular vorausfüllen
watch(() => props.order, (o) => {
  if (!o) return
  if (o.deadline) {
    const d = new Date(o.deadline)
    const pad = (n) => String(n).padStart(2, '0')
    deadlineDate.value = `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`
    deadlineTime.value = `${pad(d.getHours())}:${pad(d.getMinutes())}`
    deadlineDateMode.value = 'datum'
  }
  Object.assign(form, { ...o })
}, { immediate: true })

function formatDeadline(iso) {
  return new Date(iso).toLocaleString('de-DE', { dateStyle: 'short', timeStyle: 'short' })
}

const showHistory = ref(false)
const historyLoading = ref(false)
const history = ref([])

function statusText(status) {
  return status === 'erwartete_rueckfahrt' ? 'erwartete Rückfahrt' : status
}

// Historie bei jedem Aufklappen frisch aus der DB laden
async function toggleHistory() {
  showHistory.value = !showHistory.value
  if (!showHistory.value) return
  historyLoading.value = true
  try {
    history.value = await api.get(`/orders/${props.order.id}/history`)
  } catch {
    history.value = []
  } finally {
    historyLoading.value = false
  }
}

onMounted(async () => {
  try {
    const cfg = await api.get('/config')
    suggestions.value = cfg.destination_suggestions ?? []
    if (!props.order) {
      deadlineTime.value = cfg.default_deadline_time ?? '17:00'
    }
  } catch {
    // Fallback bleibt 17:00
  }
})

async function submit() {
  saving.value = true
  error.value = null
  try {
    const deadline = new Date(`${resolvedDeadlineDate()}T${deadlineTime.value}:00`).toISOString()
    const payload = {
      ...form,
      deadline,
      create_return_order: form.trip_type === 'hinfahrt' ? !!form.create_return_order : false,
      patient_name: form.trip_type === 'besorgung' ? null : (form.patient_name || null),
      phone: form.phone || null,
      destination_street: form.destination_street || null,
      destination_city: form.destination_city || null,
      notes: form.notes || null,
      requester_station: form.requester_station || null,
    }
    if (props.order) {
      await ordersStore.update(props.order.id, payload)
    } else {
      await ordersStore.create(payload)
    }
    emit('saved')
  } catch (e) {
    error.value = e.message
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,.4);
  display: flex; align-items: center; justify-content: center;
  z-index: 100;
}
.modal {
  background: #fff;
  border-radius: 10px;
  width: 480px;
  max-width: 95vw;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 32px rgba(0,0,0,.2);
}
.modal__header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #eee;
}
.modal__header h3 { font-size: 16px; }
.modal__body { padding: 20px; overflow-y: auto; flex: 1; }
.fields { border: none; }
.fields:disabled input, .fields:disabled select, .fields:disabled textarea { background: #f5f5f5; color: #555; }
.deadline-static { font-size: 14px; color: #555; padding: 4px 0; }
.modal__footer { display: flex; justify-content: flex-end; gap: 10px; padding-top: 16px; border-top: 1px solid #eee; margin-top: 8px; }
.field--toggle label { display: flex; align-items: center; gap: 8px; cursor: pointer; }
.field--toggle input { width: auto; }
.error { color: #c62828; font-size: 13px; margin-bottom: 10px; }

.history { margin-top: 4px; }
.history__toggle {
  background: none; border: none; padding: 0;
  font-size: 13px; color: #1565c0; cursor: pointer;
}
.history__list { margin-top: 8px; display: flex; flex-direction: column; gap: 4px; }
.history__entry { display: flex; gap: 10px; font-size: 12px; color: #555; }
.history__time { color: #888; white-space: nowrap; }
.history__user { font-weight: 600; white-space: nowrap; }
.history__change { flex: 1; }
.history__empty { font-size: 12px; color: #aaa; }
.deadline-row { display: flex; flex-direction: column; gap: 8px; }
.deadline-date-btns { display: flex; gap: 6px; }
.btn-date {
  flex: 1;
  padding: 6px 10px;
  border: 1px solid #d0d0d0;
  border-radius: 6px;
  background: #fff;
  font-size: 13px;
  cursor: pointer;
  color: #333;
}
.btn-date:hover { border-color: #1565c0; color: #1565c0; }
.btn-date--active { border-color: #1565c0; background: #e3f0ff; color: #1565c0; font-weight: 600; }
.deadline-date-input { width: 100%; }
.deadline-time-input { width: 100%; }

.autocomplete-wrap { position: relative; }
.autocomplete-wrap input { width: 100%; }
.autocomplete-list {
  position: absolute; top: 100%; left: 0; right: 0; z-index: 200;
  background: #fff; border: 1px solid #d0d0d0; border-radius: 6px;
  margin-top: 2px; list-style: none; padding: 4px 0;
  box-shadow: 0 4px 12px rgba(0,0,0,.12); max-height: 220px; overflow-y: auto;
}
.autocomplete-list li {
  padding: 8px 12px; cursor: pointer; display: flex; flex-direction: column; gap: 2px;
}
.autocomplete-list li:hover,
.autocomplete-list__item--active { background: #e3f0ff; }
.ac-name { font-size: 14px; font-weight: 600; color: #111; }
.ac-addr { font-size: 12px; color: #666; }
</style>
