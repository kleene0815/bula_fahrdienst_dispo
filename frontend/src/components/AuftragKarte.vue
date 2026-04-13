<template>
  <div
    class="karte"
    :class="[`karte--${order.priority}`, { 'karte--nicht-ziehbar': order.status !== 'offen' }]"
    :draggable="order.status === 'offen'"
    @dragstart="onDragStart"
  >
    <div class="karte__header">
      <span class="priority-dot" :class="`priority-dot--${order.priority}`"></span>
      <span class="karte__ziel">{{ order.destination }}</span>
      <span :class="`badge badge--${order.status}`">{{ order.status }}</span>
    </div>
    <div class="karte__meta">
      <span>{{ formatDeadline(order.deadline) }}</span>
      <span v-if="order.destination_address" class="karte__addr">{{ order.destination_address }}</span>
    </div>
    <div v-if="order.patient_name" class="karte__patient">
      👤 {{ order.patient_name }}
      <span v-if="order.companion" title="Begleitperson"> +1</span>
    </div>
    <div class="karte__footer">
      <span :class="`badge badge--${order.trip_type}`">{{ tripTypeLabel }}</span>
      <div class="karte__actions">
        <button
          v-if="order.status === 'offen' || order.status === 'zugeteilt'"
          class="btn-icon btn-icon--primary"
          title="Bearbeiten"
          @click.stop="$emit('edit')"
        >✏</button>
        <button
          v-if="order.status !== 'storniert' && order.status !== 'erledigt'"
          class="btn-icon btn-icon--ghost-danger"
          title="Stornieren"
          @click.stop="onCancel"
        >✕</button>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({ order: Object })
const emit = defineEmits(['cancel', 'edit'])

const tripTypeLabels = { besorgung: 'Besorgung', hinfahrt: 'Hinfahrt', abholung: 'Abholung' }
const tripTypeLabel = tripTypeLabels[props.order.trip_type] ?? props.order.trip_type

function onCancel() {
  if (!confirm('Auftrag wirklich stornieren?')) return
  emit('cancel')
}

function onDragStart(event) {
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('order-id', props.order.id)
}

function formatDeadline(iso) {
  return new Date(iso).toLocaleString('de-DE', { dateStyle: 'short', timeStyle: 'short' })
}
</script>

<style scoped>
.karte {
  background: #fff;
  border-radius: 8px;
  border-left: 4px solid #ccc;
  padding: 10px 12px;
  box-shadow: 0 1px 3px rgba(0,0,0,.08);
}
.karte[draggable="true"] {
  cursor: grab;
}
.karte[draggable="true"]:active {
  cursor: grabbing;
  opacity: 0.7;
}
.karte--nicht-ziehbar {
  cursor: not-allowed;
}
.karte--hoch   { border-left-color: #c62828; }
.karte--normal { border-left-color: #1565c0; }
.karte--gering { border-left-color: #ccc; }

.karte__header { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
.karte__ziel { flex: 1; font-weight: 600; font-size: 14px; }

.priority-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.priority-dot--hoch   { background: #c62828; }
.priority-dot--normal { background: #1565c0; }
.priority-dot--gering { background: #ccc; }

.karte__meta { font-size: 12px; color: #666; margin-bottom: 4px; display: flex; gap: 12px; }
.karte__addr { color: #888; }
.karte__patient { font-size: 12px; color: #444; margin-bottom: 6px; }
.karte__footer { display: flex; align-items: center; justify-content: space-between; }
.karte__actions { display: flex; gap: 4px; }

.btn-icon {
  padding: 4px 8px;
  font-size: 13px;
  border-radius: 4px;
  line-height: 1;
  border: none;
}
.btn-icon--primary {
  background: #1565c0;
  color: #fff;
}
.btn-icon--ghost-danger {
  background: transparent;
  color: #999;
  border: 1px solid #ddd;
}
.btn-icon--ghost-danger:hover {
  color: #c62828;
  border-color: #c62828;
}
</style>
