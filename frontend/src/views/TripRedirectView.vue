<template>
  <div class="loading-screen">
    <p v-if="error">{{ error }}</p>
    <p v-else>Fahrt wird geladen…</p>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { api } from '@/api/client'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const error = ref(null)

onMounted(async () => {
  try {
    const trip = await api.get(`/trips/by-token/${route.params.qrToken}`)
    // Fahrer-Ansicht direkt zur spezifischen Fahrt
    router.replace({ name: 'fahrer', query: { tripId: trip.id } })
  } catch (e) {
    error.value = 'Fahrt nicht gefunden oder kein Zugriff.'
  }
})
</script>
