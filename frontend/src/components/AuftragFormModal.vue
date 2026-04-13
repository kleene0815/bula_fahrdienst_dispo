<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal">
      <div class="modal__header">
        <h3>{{ order ? 'Auftrag bearbeiten' : 'Neuer Auftrag' }}</h3>
        <button class="btn-ghost" @click="$emit('close')">✕</button>
      </div>
      <form class="modal__body" @submit.prevent="submit">
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
          <input v-model="form.destination" type="text" required placeholder="z.B. Apotheke am Markt" />
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
          <label>Deadline / Termin *</label>
          <div class="deadline-row">
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
              required
              class="deadline-date-input"
            />
            <input
              v-model="deadlineTime"
              type="time"
              required
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

        <div class="field">
          <label>Bemerkungen für den Fahrer</label>
          <textarea v-model="form.notes" rows="3"></textarea>
        </div>

        <p v-if="error" class="error">{{ error }}</p>
        <div class="modal__footer">
          <button type="button" class="btn-ghost" @click="$emit('close')">Abbrechen</button>
          <button type="submit" class="btn-primary" :disabled="saving">
            {{ saving ? 'Wird gespeichert…' : 'Speichern' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, watch, onMounted } from 'vue'
import { useOrdersStore } from '@/stores/orders'
import { api } from '@/api/client'

const props = defineProps({ order: Object })
const emit = defineEmits(['saved', 'close'])
const ordersStore = useOrdersStore()
const saving = ref(false)
const error = ref(null)

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
  const d = new Date(o.deadline)
  const pad = (n) => String(n).padStart(2, '0')
  deadlineDate.value = `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`
  deadlineTime.value = `${pad(d.getHours())}:${pad(d.getMinutes())}`
  deadlineDateMode.value = 'datum'
  Object.assign(form, { ...o })
}, { immediate: true })

onMounted(async () => {
  if (!props.order) {
    try {
      const cfg = await api.get('/config')
      deadlineTime.value = cfg.default_deadline_time ?? '17:00'
    } catch {
      // Fallback bleibt 17:00
    }
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
.modal__footer { display: flex; justify-content: flex-end; gap: 10px; padding-top: 16px; border-top: 1px solid #eee; margin-top: 8px; }
.field--toggle label { display: flex; align-items: center; gap: 8px; cursor: pointer; }
.field--toggle input { width: auto; }
.error { color: #c62828; font-size: 13px; margin-bottom: 10px; }
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
</style>
