<template>
  <RouterView v-if="auth.ready" />
  <div v-else class="loading-screen">
    <p>Anmeldung wird durchgeführt…</p>
  </div>
</template>

<script setup>
import { RouterView } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
</script>

<style>
* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: system-ui, -apple-system, sans-serif;
  font-size: 14px;
  background: #f5f5f5;
  color: #1a1a1a;
}

.loading-screen {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  color: #666;
}

/* Globale Hilfklassen */
.badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}
.badge--offen      { background: #e3f2fd; color: #1565c0; }
.badge--zugeteilt  { background: #fff3e0; color: #e65100; }
.badge--unterwegs  { background: #fff8e1; color: #f57f17; }
.badge--erledigt   { background: #e8f5e9; color: #2e7d32; }
.badge--storniert  { background: #f5f5f5; color: #757575; }
.badge--geplant    { background: #e3f2fd; color: #1565c0; }
.badge--aktiv      { background: #fff3e0; color: #e65100; }
.badge--abgeschlossen { background: #e8f5e9; color: #2e7d32; }
.badge--abgebrochen   { background: #f5f5f5; color: #757575; }

.badge--normal { background: #f5f5f5; color: #555; }
.badge--mittel { background: #fff3e0; color: #e65100; }
.badge--hoch   { background: #ffebee; color: #c62828; }

button {
  cursor: pointer;
  border: none;
  border-radius: 6px;
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 500;
}
button:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-primary  { background: #1565c0; color: #fff; }
.btn-success  { background: #2e7d32; color: #fff; }
.btn-danger   { background: #c62828; color: #fff; }
.btn-ghost    { background: transparent; color: #1565c0; border: 1px solid #1565c0; }

input, select, textarea {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #ccc;
  border-radius: 6px;
  font-size: 14px;
  font-family: inherit;
}
input:focus, select:focus, textarea:focus {
  outline: 2px solid #1565c0;
  border-color: transparent;
}

label { display: block; font-weight: 500; margin-bottom: 4px; color: #444; }
.field { margin-bottom: 14px; }
</style>
