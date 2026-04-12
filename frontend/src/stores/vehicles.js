import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/api/client'

export const useVehiclesStore = defineStore('vehicles', () => {
  const vehicles = ref([])

  async function fetchAll(activeOnly = true) {
    vehicles.value = await api.get(`/vehicles?active_only=${activeOnly}`)
  }

  async function create(data) {
    const v = await api.post('/vehicles', data)
    vehicles.value.push(v)
    return v
  }

  async function update(id, data) {
    const v = await api.patch(`/vehicles/${id}`, data)
    const idx = vehicles.value.findIndex((x) => x.id === id)
    if (idx >= 0) vehicles.value[idx] = v
    return v
  }

  return { vehicles, fetchAll, create, update }
})
