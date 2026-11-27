import { useEffect, useState } from 'react'
import Chat from './Chat'
import { getMe, listConversations, type ConversationSummary, type User } from './api'
import './App.css'

export default function App() {
  const [user, setUser] = useState<User | null>(null)
  const [conversations, setConversations] = useState<ConversationSummary[]>([])
  const [listError, setListError] = useState('')
  const [activeId, setActiveId] = useState<string | null>(null)
  const [chatOpen, setChatOpen] = useState(false)
  const [chatKey, setChatKey] = useState('new')

  function refreshList() {
    listConversations()
      .then((list) => {
        setConversations(list)
        setListError('')
      })
      .catch(() => setListError('Could not load your conversations.'))
  }

  useEffect(() => {
    getMe()
      .then(setUser)
      .catch(() => setUser({ id: 'guest', name: 'Guest' }))
    refreshList()
  }, [])

  function openConversation(id: string | null) {
    setActiveId(id)
    setChatKey(id ?? `new-${Date.now()}`)
    setChatOpen(true)
  }

  return (
    <div className="page">
      <header className="topbar">
        <div>
          <p className="eyebrow">Welcome back</p>
          <h1>Hello {user?.name ?? '...'}</h1>
        </div>
        <div className="avatar" aria-hidden>
          {user?.name[0] ?? ''}
        </div>
      </header>

      <section className="card">
        <div className="card-header">
          <h2>Your conversations</h2>
          <button className="primary" onClick={() => openConversation(null)}>
            + New chat
          </button>
        </div>

        {listError && <p className="error">{listError}</p>}
        {!listError && conversations.length === 0 && (
          <p className="empty">No conversations yet. Start one with the chat button.</p>
        )}
        <ul className="conversation-list">
          {conversations.map((c) => (
            <li key={c.id}>
              <button
                className={c.id === activeId && chatOpen ? 'active' : ''}
                onClick={() => openConversation(c.id)}
              >
                <span className="title">{c.title}</span>
                <span className="meta">
                  {new Date(c.updated_at).toLocaleDateString(undefined, {
                    month: 'short',
                    day: 'numeric',
                  })}
                </span>
              </button>
            </li>
          ))}
        </ul>
      </section>

      {/* A new key per conversation resets the chat window's state. A brand-new
          chat keeps the key "new" after its first save, so it doesn't reload. */}
      <Chat
        key={chatKey}
        conversationId={activeId}
        open={chatOpen}
        onToggle={() => setChatOpen(!chatOpen)}
        onNewChat={() => openConversation(null)}
        onSaved={(id) => {
          setActiveId(id)
          refreshList()
        }}
      />
    </div>
  )
}
