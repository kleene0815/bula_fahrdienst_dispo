import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/api/client'

export const useTripsStore = defineStore('trips', () => {
  const trips = ref([])
  const myTrips = ref([])
  const loading = ref(false)

  async function fetchAll() {
    loading.value = true
    try {
      trips.value = await api.get('/trips')
    } finally {
      loading.value = false
    }
  }

  async function fetchMine() {
    myTrips.value = await api.get('/trips/mine')
  }

  async function fetchByToken(qrToken) {
    return api.get(`/trips/by-token/${qrToken}`)
  }

  async function create(data) {
    const trip = await api.post('/trips', data)
    const idx = trips.value.findIndex((t) => t.id === trip.id)
    if (idx >= 0) {
      trips.value[idx] = trip
    } else {
      trips.value.push(trip)
    }
    return trip
  }

  async function update(id, data) {
    const trip = await api.patch(`/trips/${id}`, data)
    _replace(trip)
    return trip
  }

  async function start(id) {
    const trip = await api.post(`/trips/${id}/start`)
    _replace(trip)
    _replaceMine(trip)
    return trip
  }

  async function completeStop(tripId, orderId) {
    const trip = await api.post(`/trips/${tripId}/orders/${orderId}/complete`)
    _replace(trip)
    _replaceMine(trip)
    return trip
  }

  async function complete(id) {
    const trip = await api.post(`/trips/${id}/complete`)
    _replace(trip)
    _replaceMine(trip)
    return trip
  }

  async function abort(id) {
    const trip = await api.post(`/trips/${id}/abort`)
    _replace(trip)
    return trip
  }

  // Vom SSE-Stream aufgerufen
  function applyEvent(eventType, data) {
    if (eventType === 'trip_created') {
      if (!trips.value.find((t) => t.id === data.id)) {
        trips.value.push(data)
      }
    } else if (eventType === 'trip_updated') {
      _replace(data)
    }
  }

  function _replace(trip) {
    const idx = trips.value.findIndex((t) => t.id === trip.id)
    if (idx >= 0) trips.value[idx] = trip
  }

  function _replaceMine(trip) {
    const idx = myTrips.value.findIndex((t) => t.id === trip.id)
    if (idx >= 0) myTrips.value[idx] = trip
  }

  return { trips, myTrips, loading, fetchAll, fetchMine, fetchByToken, create, update, start, completeStop, complete, abort, applyEvent }
})
