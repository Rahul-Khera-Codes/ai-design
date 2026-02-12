import { API_BASE } from './api.js'

/**
 * Send a chat message to the chatbot
 */
export async function sendChatMessage(message, sessionId = null) {
  const res = await fetch(`${API_BASE}/api/chatbot/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({
      message,
      session_id: sessionId,
    }),
  })

  const data = await res.json().catch(() => ({}))

  if (!res.ok) {
    throw new Error(data.detail || data.message || 'Failed to send message')
  }

  return data
}

/**
 * Start a design flow
 */
export async function startDesignFlow(userId = null, initialPreferences = {}) {
  const res = await fetch(`${API_BASE}/api/chatbot/design/start`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({
      user_id: userId,
      initial_preferences: initialPreferences,
    }),
  })

  const data = await res.json().catch(() => ({}))

  if (!res.ok) {
    throw new Error(data.detail || data.message || 'Failed to start design flow')
  }

  return data
}

/**
 * Process a design step
 */
export async function processDesignStep(sessionId, answer, userId = null) {
  const res = await fetch(`${API_BASE}/api/chatbot/design/step`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({
      session_id: sessionId,
      answer,
      user_id: userId,
    }),
  })

  const data = await res.json().catch(() => ({}))

  if (!res.ok) {
    throw new Error(data.detail || data.message || 'Failed to process design step')
  }

  return data
}

/**
 * Get conversation history
 */
export async function getConversationHistory(sessionId) {
  const res = await fetch(`${API_BASE}/api/chatbot/history/${sessionId}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  })

  const data = await res.json().catch(() => ({}))

  if (!res.ok) {
    throw new Error(data.detail || data.message || 'Failed to get history')
  }

  return data
}
