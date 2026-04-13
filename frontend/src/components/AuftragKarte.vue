<template>
  <div class="karte" :class="`karte--${order.priority}`">
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
      <span class="karte__id">{{ order.id.slice(0, 8) }}</span>
      <div class="karte__actions">
        <button
          v-if="order.status === 'offen' || order.status === 'zugeteilt'"
          class="btn-ghost"
          style="padding: 4px 10px; font-size: 12px"
          @click.stop="$emit('edit')"
        >Bearbeiten</button>
        <button
          v-if="order.status !== 'storniert' && order.status !== 'erledigt'"
          class="btn-danger"
          style="padding: 4px 10px; font-size: 12px"
          @click.stop="$emit('cancel')"
        >Stornieren</button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({ order: Object })
defineEmits(['cancel', 'edit'])

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
.karte__id { font-size: 11px; color: #bbb; font-family: monospace; }
.karte__actions { display: flex; gap: 6px; }
</style>
