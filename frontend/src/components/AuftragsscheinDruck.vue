<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal">
      <div class="modal__actions no-print">
        <button class="btn-primary" @click="window.print()">🖨 Drucken</button>
        <button class="btn-ghost" @click="$emit('close')">Schließen</button>
      </div>

      <div class="druckansicht" id="druckansicht">
        <!-- Kopfbereich -->
        <header class="druck-header">
          <div class="druck-header__left">
            <h1>Auftragsschein</h1>
            <p>Fahrt #{{ trip.trip_number }} · {{ formatDate(trip.created_at) }}</p>
            <p>Fahrer: <strong>{{ trip.driver?.name }}</strong></p>
            <p>Fahrzeug: <strong>{{ trip.vehicle?.name }}</strong> ({{ trip.vehicle?.license_plate }})</p>
          </div>
          <div class="druck-header__qr">
            <img v-if="qrDataUrl" :src="qrDataUrl" alt="QR-Code" width="100" height="100" />
          </div>
        </header>

        <!-- Auftragstabelle -->
        <table class="auftrag-tabelle">
          <thead>
            <tr>
              <th>#</th>
              <th>Ziel</th>
              <th>Typ</th>
              <th>Termin</th>
              <th>Patient</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="to in trip.orders" :key="to.order.id">
              <td>{{ to.sort_order }}</td>
              <td>
                {{ to.order.destination }}
                <br v-if="to.order.destination_address" />
                <small v-if="to.order.destination_address" style="color:#888">{{ to.order.destination_address }}</small>
              </td>
              <td><span class="type-badge">{{ to.order.trip_type }}</span></td>
              <td>{{ formatDatetime(to.order.deadline) }}</td>
              <td>
                <span v-if="to.order.patient_name">
                  {{ to.order.patient_name }}<span v-if="to.order.companion"> + Begl.</span>
                </span>
              </td>
            </tr>
          </tbody>
        </table>

        <div v-if="trip.notes" class="druck-notizen">
          <strong>Hinweise:</strong> {{ trip.notes }}
        </div>

        <!-- Patientenabschnitte (nur für hinfahrt) -->
        <template v-for="to in hinfahrtOrders" :key="`patient-${to.order.id}`">
          <div class="trennlinie">
            <span>✂ Abtrennen</span>
          </div>

          <div class="patientenabschnitt">
            <div class="patientenabschnitt__header">
              <strong>Patientenbegleitschein</strong>
              <span>Fahrt #{{ trip.trip_number }}</span>
            </div>
            <table class="patient-tabelle">
              <tbody>
                <tr>
                  <td><strong>Ziel</strong></td>
                  <td>{{ to.order.destination }}</td>
                </tr>
                <tr v-if="to.order.destination_address">
                  <td><strong>Adresse</strong></td>
                  <td>{{ to.order.destination_address }}</td>
                </tr>
                <tr>
                  <td><strong>Termin</strong></td>
                  <td>{{ formatDatetime(to.order.deadline) }}</td>
                </tr>
                <tr>
                  <td><strong>Patient</strong></td>
                  <td>{{ to.order.patient_name }}<span v-if="to.order.companion"> (+ Begleitperson)</span></td>
                </tr>
              </tbody>
            </table>
            <div class="patientenabschnitt__footer">
              <div>
                <strong>{{ config.security_center_name }}</strong><br />
                Tel: {{ config.security_center_phone }}
              </div>
              <div>
                {{ config.organizer_name }}<br />
                {{ config.camp_address }}
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '@/api/client'

const props = defineProps({ trip: Object })
defineEmits(['close'])

const config = ref({})
const qrDataUrl = ref(null)

const hinfahrtOrders = computed(() =>
  props.trip.orders.filter((to) => to.order.trip_type === 'hinfahrt')
)

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('de-DE')
}
function formatDatetime(iso) {
  return new Date(iso).toLocaleString('de-DE', { dateStyle: 'short', timeStyle: 'short' })
}

async function generateQR() {
  // QR-Code als Data-URL via Canvas erzeugen (ohne externe Bibliothek)
  // Für Produktion: qrcode-Bibliothek einbinden
  const url = `${window.location.origin}/trip/${props.trip.qr_token}`
  try {
    const QRCode = (await import('qrcode')).default
    qrDataUrl.value = await QRCode.toDataURL(url, { width: 100 })
  } catch {
    // qrcode-Bibliothek nicht verfügbar — QR-Code-Feld bleibt leer
  }
}

onMounted(async () => {
  try {
    const data = await api.get(`/trips/${props.trip.id}/printout`)
    config.value = data.config
  } catch {
    config.value = {}
  }
  await generateQR()
})
</script>

<style scoped>
.modal-overlay { position:fixed;inset:0;background:rgba(0,0,0,.5);display:flex;align-items:flex-start;justify-content:center;z-index:200;overflow-y:auto;padding:20px; }
.modal { background:#fff;width:210mm;max-width:95vw;border-radius:8px;overflow:hidden; }
.modal__actions { display:flex;gap:10px;padding:12px 20px;background:#f5f5f5;border-bottom:1px solid #ddd; }

.druckansicht { padding:20mm; font-size:12pt; line-height:1.4; }

.druck-header { display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:16px;padding-bottom:12px;border-bottom:2px solid #000; }
.druck-header h1 { font-size:18pt;margin-bottom:4px; }
.druck-header p { margin-bottom:2px; }

.auftrag-tabelle { width:100%;border-collapse:collapse;margin-bottom:12px; }
.auftrag-tabelle th { background:#f0f0f0;padding:6px 8px;text-align:left;border:1px solid #ccc;font-size:10pt; }
.auftrag-tabelle td { padding:6px 8px;border:1px solid #ddd;vertical-align:top; }
.type-badge { background:#eee;padding:1px 6px;border-radius:4px;font-size:10pt; }

.druck-notizen { padding:8px;background:#fffde7;border:1px solid #f9a825;border-radius:4px;margin-bottom:16px;font-size:11pt; }

.trennlinie {
  display:flex;align-items:center;gap:8px;margin:16px 0;
  font-size:10pt;color:#888;
}
.trennlinie::before,.trennlinie::after { content:'';flex:1;border-top:1px dashed #aaa; }

.patientenabschnitt { border:1px solid #ccc;border-radius:6px;padding:12px; }
.patientenabschnitt__header { display:flex;justify-content:space-between;margin-bottom:10px;font-size:13pt; }
.patient-tabelle { width:100%;border-collapse:collapse;margin-bottom:10px; }
.patient-tabelle td { padding:4px 8px;border-bottom:1px solid #eee; }
.patient-tabelle td:first-child { width:100px;color:#666; }
.patientenabschnitt__footer { display:flex;justify-content:space-between;padding-top:10px;border-top:1px solid #eee;font-size:10pt; }

@media print {
  .no-print { display:none !important; }
  .modal-overlay { position:static;background:none;padding:0; }
  .modal { width:100%;border-radius:0;box-shadow:none; }
  .druckansicht { padding:10mm; }
}
</style>
