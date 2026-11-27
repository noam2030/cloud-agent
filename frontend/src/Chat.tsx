import { useEffect, useRef, useState, type FormEvent } from 'react'

type Message = { role: 'user' | 'assistant'; content: string }

// Set at build time. Vercel reads it from its project settings.
const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function send(e: FormEvent) {
    e.preventDefault()
    const text = input.trim()
    if (!text || loading) return

    // The backend keeps no state, so every request carries the whole conversation.
    const history: Message[] = [...messages, { role: 'user', content: text }]
    setMessages(history)
    setInput('')
    setError('')
    setLoading(true)

    try {
      const res = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: history }),
      })
      if (!res.ok) throw new Error(`Server returned ${res.status}`)
      const data: { reply: string } = await res.json()
      setMessages([...history, { role: 'assistant', content: data.reply }])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="chat">
      <div className="messages">
        {messages.map((m, i) => (
          <div key={i} className={`message ${m.role}`}>
            {m.content}
          </div>
        ))}
        {loading && <div className="message assistant">Thinking...</div>}
        <div ref={bottomRef} />
      </div>
      {error && <p className="error">{error}</p>}
      <form onSubmit={send}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question"
          autoFocus
        />
        <button type="submit" disabled={loading || !input.trim()}>
          Send
        </button>
      </form>
    </section>
  )
}
