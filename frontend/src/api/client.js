/**
 * Zentraler API-Client. Hängt den Keycloak-Token automatisch als Bearer an.
 * Basis-URL wird aus dem Vite-Proxy bedient (/api → http://localhost:8000/api).
 */

const BASE = '/api/v1'

async function getToken() {
  const { useAuthStore } = await import('@/stores/auth')
  const auth = useAuthStore()
  await auth.refreshIfExpired()
  return auth.token
}

async function request(method, path, body = undefined) {
  const token = await getToken()
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw Object.assign(new Error(err.detail ?? 'Fehler'), { status: res.status })
  }

  if (res.status === 204) return null
  return res.json()
}

export const api = {
  get: (path) => request('GET', path),
  post: (path, body) => request('POST', path, body),
  patch: (path, body) => request('PATCH', path, body),
  put: (path, body) => request('PUT', path, body),
  delete: (path) => request('DELETE', path),

  // Server-Sent Events — gibt EventSource zurück
  sse(path) {
    return getToken().then((token) => {
      // Token als Query-Parameter, da EventSource keine Custom-Header unterstützt
      return new EventSource(`${BASE}${path}?token=${encodeURIComponent(token)}`)
    })
  },
}
