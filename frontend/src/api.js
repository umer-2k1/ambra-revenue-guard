// Thin API client. In dev, `/api` is proxied to the backend by Vite
// (see vite.config.js). In production (separate frontend/backend projects),
// set VITE_API_BASE_URL to the backend origin, e.g. https://ambra-api.vercel.app
const API_BASE = import.meta.env.VITE_API_BASE_URL
  ? `${import.meta.env.VITE_API_BASE_URL.replace(/\/$/, '')}/api`
  : '/api'

async function getJSON(path) {
  const res = await fetch(`${API_BASE}${path}`)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

export const getDenials = () => getJSON('/denials')
export const getDenialStats = () => getJSON('/denials/stats')
export const getRules = () => getJSON('/rules')
export const getStatus = () => getJSON('/status')
export const getDemoClaim = () => getJSON('/demo-claim')

export async function scoreClaim(claim) {
  const res = await fetch(`${API_BASE}/score`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(claim),
  })
  const data = await res.json()
  if (!res.ok) throw new Error(data?.error || `${res.status} ${res.statusText}`)
  return data
}

export async function resetSystem() {
  const res = await fetch(`${API_BASE}/reset`, { method: 'POST' })
  return res.json()
}

/**
 * POST /api/analyze and parse the Server-Sent Events stream.
 * EventSource can't do POST, so we read the body as a stream.
 */
export async function startAnalysis(onProgress) {
  const res = await fetch(`${API_BASE}/analyze`, { method: 'POST' })
  if (!res.ok) {
    let message = `${res.status} ${res.statusText}`
    try {
      const body = await res.json()
      if (body?.error) message = body.error
    } catch {
      /* ignore */
    }
    throw new Error(message)
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''

    for (const line of lines) {
      const trimmed = line.trim()
      if (trimmed.startsWith('data:')) {
        const payload = trimmed.slice(5).trim()
        if (!payload) continue
        try {
          onProgress(JSON.parse(payload))
        } catch {
          /* ignore malformed chunk */
        }
      }
    }
  }
}
