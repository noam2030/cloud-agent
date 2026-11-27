import Chat from './Chat'
import './App.css'

// Placeholder content so the page has something behind the chat window.
const items = Array.from({ length: 20 }, (_, i) => ({
  id: i + 1,
  title: `Item ${i + 1}`,
  description: 'A sample list item.',
}))

export default function App() {
  return (
    <main className="page">
      <h1>Hello World</h1>
      <ul className="list">
        {items.map((item) => (
          <li key={item.id}>
            <strong>{item.title}</strong>
            <span>{item.description}</span>
          </li>
        ))}
      </ul>
      <Chat />
    </main>
  )
}
