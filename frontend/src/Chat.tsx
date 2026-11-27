import { useEffect, useRef, useState, type FormEvent } from 'react'
import { getConversation, sendMessage, type Message } from './api'

type Props = {
  conversationId: string | null // null = a new, empty chat
  open: boolean
  onToggle: () => void
  onNewChat: () => void
  onSaved: (conversationId: string) => void
}

export default function Chat({ conversationId, open, onToggle, onNewChat, onSaved }: Props) {
  const [messages, setMessages] = useState<Message[]>([])
  // An existing conversation starts "loading" until its messages arrive.
  const [fetching, setFetching] = useState(conversationId !== null)
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  // App gives Chat a new `key` per conversation, so this runs once per conversation.
  useEffect(() => {
    if (conversationId === null) return
    getConversation(conversationId)
      .then((c) => setMessages(c.messages))
      .catch(() => setError('Could not load this conversation.'))
      .finally(() => setFetching(false))
    // Only on mount: after a send, the messages on screen are already current.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading, open])

  async function send(e: FormEvent) {
    e.preventDefault()
    const text = input.trim()
    if (!text || loading) return

    // Show the question right away; the server saves it with the answer.
    setMessages((prev) => [...prev, { role: 'user', content: text }])
    setInput('')
    setError('')
    setLoading(true)

    try {
      const res = await sendMessage(conversationId, text)
      setMessages((prev) => [...prev, { role: 'assistant', content: res.reply }])
      onSaved(res.conversation_id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={`chat-widget ${open ? 'is-open' : ''}`}>
      {open && (
        <section className="chat" aria-label="Chat">
          <header>
            <strong>Ask AI</strong>
            <div className="header-actions">
              <button type="button" onClick={onNewChat} aria-label="New chat" title="New chat">
                +
              </button>
              <button type="button" onClick={onToggle} aria-label="Close chat" title="Close">
                ×
              </button>
            </div>
          </header>
          <div className="messages">
            {messages.length === 0 && !loading && !fetching && (
              <p className="hint">Ask me anything to start a conversation.</p>
            )}
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
              placeholder="Type your question..."
              autoFocus
            />
            <button type="submit" disabled={loading || !input.trim()} aria-label="Send">
              ➤
            </button>
          </form>
        </section>
      )}
      <button
        type="button"
        className="chat-toggle"
        onClick={onToggle}
        aria-label={open ? 'Hide chat' : 'Open chat'}
      >
        {open ? '×' : '💬'}
      </button>
    </div>
  )
}
