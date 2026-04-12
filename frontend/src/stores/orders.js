import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/api/client'

export const useOrdersStore = defineStore('orders', () => {
  const orders = ref([])
  const loading = ref(false)

  async function fetchAll(status = null) {
    loading.value = true
    try {
      const path = status ? `/orders?status=${status}` : '/orders'
      orders.value = await api.get(path)
    } finally {
      loading.value = false
    }
  }

  async function create(data) {
    const order = await api.post('/orders', data)
    orders.value.push(order)
    return order
  }

  async function update(id, data) {
    const order = await api.patch(`/orders/${id}`, data)
    _replace(order)
    return order
  }

  async function cancel(id) {
    const order = await api.post(`/orders/${id}/cancel`)
    _replace(order)
    return order
  }

  // Vom SSE-Stream aufgerufen
  function applyEvent(eventType, data) {
    if (eventType === 'order_created') {
      orders.value.push(data)
    } else if (eventType === 'order_updated') {
      _replace(data)
    }
  }

  function _replace(order) {
    const idx = orders.value.findIndex((o) => o.id === order.id)
    if (idx >= 0) orders.value[idx] = order
  }

  return { orders, loading, fetchAll, create, update, cancel, applyEvent }
})
