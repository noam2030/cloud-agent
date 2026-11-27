// All calls to the backend. The backend owns the data; the browser only displays it.

// Set at build time. Vercel reads it from its project settings.
const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export type User = { id: string; name: string }
export type Message = { role: 'user' | 'assistant'; content: string }
export type ConversationSummary = { id: string; title: string; updated_at: string }
export type Conversation = ConversationSummary & { messages: Message[] }

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json' },
  })
  if (!res.ok) throw new Error(`Server returned ${res.status}`)
  return res.json()
}

export const getMe = () => request<User>('/api/me')
export const listConversations = () => request<ConversationSummary[]>('/api/conversations')
export const getConversation = (id: string) => request<Conversation>(`/api/conversations/${id}`)

// Sends only the new message. The backend loads the history, asks the model, and saves both.
export const sendMessage = (conversationId: string | null, message: string) =>
  request<{ conversation_id: string; reply: string }>('/api/chat', {
    method: 'POST',
    body: JSON.stringify({ conversation_id: conversationId, message }),
  })
