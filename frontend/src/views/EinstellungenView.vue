<template>
  <div class="einstellungen-layout">
    <header class="einstellungen-header">
      <button class="btn-ghost" @click="router.back()">← Zurück</button>
      <h1>Einstellungen</h1>
    </header>

    <div class="einstellungen-body">

      <!-- App-Konfiguration -->
      <section class="card">
        <h2>App-Konfiguration</h2>
        <form @submit.prevent="saveConfig">
          <div class="field">
            <label>Name der Sicherheitszentrale</label>
            <input v-model="config.security_center_name" type="text" />
          </div>
          <div class="field">
            <label>Telefonnummer der Sicherheitszentrale</label>
            <input v-model="config.security_center_phone" type="text" />
          </div>
          <div class="field">
            <label>Name des Veranstalters</label>
            <input v-model="config.organizer_name" type="text" />
          </div>
          <div class="field">
            <label>Adresse des Lagerplatzes</label>
            <input v-model="config.camp_address" type="text" />
          </div>
          <div class="field">
            <label>Standard-Deadline-Uhrzeit</label>
            <input v-model="config.default_deadline_time" type="time" />
          </div>
          <p v-if="configSaved" class="success">Gespeichert ✓</p>
          <button type="submit" class="btn-primary" :disabled="configSaving">
            {{ configSaving ? 'Wird gespeichert…' : 'Speichern' }}
          </button>
        </form>
      </section>

      <!-- Fahrzeugverwaltung -->
      <section class="card">
        <div class="card__header">
          <h2>Fahrzeuge</h2>
          <button class="btn-primary" @click="openNewVehicleForm">+ Neues Fahrzeug</button>
        </div>

        <table class="vehicle-table">
          <thead>
            <tr>
              <th>Bezeichnung</th>
              <th>Kennzeichen</th>
              <th>Sitze</th>
              <th>Typ</th>
              <th>Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="v in allVehicles" :key="v.id" :class="{ inactive: !v.active }">
              <td>{{ v.name }}</td>
              <td>{{ v.license_plate }}</td>
              <td>{{ v.seats }}</td>
              <td>{{ v.type }}</td>
              <td>
                <span :class="v.active ? 'badge badge--erledigt' : 'badge badge--storniert'">
                  {{ v.active ? 'Aktiv' : 'Deaktiviert' }}
                </span>
              </td>
              <td>
                <button class="btn-ghost" style="font-size:12px;padding:3px 8px" @click="editVehicle(v)">Bearbeiten</button>
                <button
                  class="btn-ghost"
                  style="font-size:12px;padding:3px 8px;margin-left:4px"
                  @click="toggleVehicleActive(v)"
                >{{ v.active ? 'Deaktivieren' : 'Aktivieren' }}</button>
              </td>
            </tr>
          </tbody>
        </table>
      </section>
    </div>
  </div>

  <!-- Fahrzeug-Modal -->
  <Teleport to="body">
    <div v-if="showVehicleForm" class="modal-backdrop" @click.self="closeVehicleForm">
      <div class="modal">
        <div class="modal__header">
          <h3>{{ editingVehicle ? 'Fahrzeug bearbeiten' : 'Neues Fahrzeug' }}</h3>
          <button class="modal__close" @click="closeVehicleForm">✕</button>
        </div>
        <div class="modal__body">
          <div class="field">
            <label>Bezeichnung *</label>
            <input v-model="vehicleForm.name" type="text" required autofocus />
          </div>
          <div class="field">
            <label>Kennzeichen *</label>
            <input v-model="vehicleForm.license_plate" type="text" required />
          </div>
          <div class="field">
            <label>Sitzanzahl (inkl. Fahrersitz) *</label>
            <input v-model.number="vehicleForm.seats" type="number" min="1" required />
          </div>
          <div class="field">
            <label>Typ *</label>
            <select v-model="vehicleForm.type">
              <option value="fest">Fest</option>
              <option value="privat">Privat</option>
            </select>
          </div>
        </div>
        <div class="modal__footer">
          <button class="btn-ghost" @click="closeVehicleForm">Abbrechen</button>
          <button class="btn-primary" @click="saveVehicle" :disabled="vehicleSaving">
            {{ vehicleSaving ? 'Wird gespeichert…' : 'Speichern' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useVehiclesStore } from '@/stores/vehicles'
import { api } from '@/api/client'

const router = useRouter()
const vehiclesStore = useVehiclesStore()

const allVehicles = ref([])
const showVehicleForm = ref(false)
const editingVehicle = ref(null)
const vehicleSaving = ref(false)
const configSaving = ref(false)
const configSaved = ref(false)

const config = reactive({
  security_center_name: '',
  security_center_phone: '',
  organizer_name: '',
  camp_address: '',
  default_deadline_time: '17:00',
})

const vehicleForm = reactive({ name: '', license_plate: '', seats: 8, type: 'fest' })

function resetVehicleForm() {
  vehicleForm.name = ''
  vehicleForm.license_plate = ''
  vehicleForm.seats = 8
  vehicleForm.type = 'fest'
}

function openNewVehicleForm() {
  editingVehicle.value = null
  resetVehicleForm()
  showVehicleForm.value = true
}

function closeVehicleForm() {
  showVehicleForm.value = false
  editingVehicle.value = null
  resetVehicleForm()
}

async function saveConfig() {
  configSaving.value = true
  configSaved.value = false
  try {
    await api.put('/config', { ...config })
    configSaved.value = true
    setTimeout(() => { configSaved.value = false }, 3000)
  } finally {
    configSaving.value = false
  }
}

function editVehicle(v) {
  editingVehicle.value = v
  Object.assign(vehicleForm, { name: v.name, license_plate: v.license_plate, seats: v.seats, type: v.type })
  showVehicleForm.value = true
}

async function toggleVehicleActive(v) {
  const updated = await vehiclesStore.update(v.id, { active: !v.active })
  const idx = allVehicles.value.findIndex((x) => x.id === v.id)
  if (idx >= 0) allVehicles.value[idx] = updated
}

async function saveVehicle() {
  vehicleSaving.value = true
  try {
    if (editingVehicle.value) {
      await vehiclesStore.update(editingVehicle.value.id, { ...vehicleForm })
    } else {
      await vehiclesStore.create({ ...vehicleForm })
    }
    closeVehicleForm()
    await loadVehicles()
  } finally {
    vehicleSaving.value = false
  }
}

async function loadVehicles() {
  allVehicles.value = await api.get('/vehicles?active_only=false')
}

onMounted(async () => {
  const [cfg] = await Promise.all([api.get('/config'), loadVehicles()])
  Object.assign(config, cfg)
})
</script>

<style scoped>
.einstellungen-layout { min-height:100vh;background:#f5f5f5; }
.einstellungen-header { display:flex;align-items:center;gap:16px;padding:14px 24px;background:#fff;border-bottom:1px solid #e0e0e0; }
.einstellungen-header h1 { font-size:18px; }
.einstellungen-body { max-width:760px;margin:0 auto;padding:24px;display:flex;flex-direction:column;gap:24px; }

.card { background:#fff;border-radius:10px;padding:20px;box-shadow:0 1px 3px rgba(0,0,0,.08); }
.card h2 { font-size:16px;margin-bottom:16px; }
.card__header { display:flex;align-items:center;justify-content:space-between;margin-bottom:16px; }
.card__header h2 { margin-bottom:0; }

.vehicle-table { width:100%;border-collapse:collapse;font-size:13px; }
.vehicle-table th { text-align:left;padding:6px 8px;color:#888;border-bottom:1px solid #eee;font-weight:500; }
.vehicle-table td { padding:8px 8px;border-bottom:1px solid #f5f5f5; }
.vehicle-table tr.inactive td { color:#bbb; }

.success { color:#2e7d32;font-size:13px;margin-bottom:10px; }

/* Modal */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: #fff;
  border-radius: 12px;
  width: 100%;
  max-width: 440px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.18);
  display: flex;
  flex-direction: column;
}

.modal__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 20px 14px;
  border-bottom: 1px solid #eee;
}

.modal__header h3 {
  font-size: 15px;
  font-weight: 600;
  margin: 0;
}

.modal__close {
  background: none;
  border: none;
  font-size: 16px;
  color: #888;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 4px;
  line-height: 1;
}

.modal__close:hover { background: #f0f0f0; color: #333; }

.modal__body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.modal__footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 14px 20px 18px;
  border-top: 1px solid #eee;
}
</style>
