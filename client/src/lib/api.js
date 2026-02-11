export const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:6789'

export async function authRequest(path, body) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include', // send/receive auth cookies
    body: JSON.stringify(body),
  })

  const data = await res.json().catch(() => ({}))

  if (!res.ok) {
    throw new Error(data.detail || data.message || 'Something went wrong')
  }

  return data
}

export async function authenticatedRequest(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    credentials: 'include', // send/receive auth cookies
  })

  const data = await res.json().catch(() => ({}))

  if (!res.ok) {
    if (res.status === 401) {
      // Redirect to login if unauthorized
      window.location.href = '/login'
    }
    throw new Error(data.detail || data.message || 'Something went wrong')
  }

  return data
}