import React, { useState, useRef, useEffect, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import Chat from './components/Chat'
import Sidebar from './components/Sidebar'
import DocumentModal from './components/DocumentModal'

const WS_BASE = window.location.hostname === 'localhost'
  ? `ws://localhost:8000`
  : `ws://${window.location.host}`

const API_BASE = window.location.hostname === 'localhost'
  ? 'http://localhost:8000'
  : ''

export default function App() {
  const [sessionId, setSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [documents, setDocuments] = useState([])
  const [bookings, setBookings] = useState([])
  const [selectedDoc, setSelectedDoc] = useState(null)
  const wsRef = useRef(null)
  const messagesEndRef = useRef(null)

  // Create session on mount
  useEffect(() => {
    fetch(`${API_BASE}/api/sessions`, { method: 'POST' })
      .then(r => r.json())
      .then(data => setSessionId(data.session_id))
      .catch(err => console.error('Failed to create session:', err))
  }, [])

  // Connect WebSocket when session is ready
  useEffect(() => {
    if (!sessionId) return

    const ws = new WebSocket(`${WS_BASE}/ws/chat/${sessionId}`)
    wsRef.current = ws

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)

      if (data.type === 'start') {
        setIsLoading(true)
      } else if (data.type === 'chunk') {
        setMessages(prev => {
          const last = prev[prev.length - 1]
          if (last && last.role === 'agent' && last.streaming) {
            return [
              ...prev.slice(0, -1),
              { ...last, content: last.content + data.content }
            ]
          }
          return [...prev, { role: 'agent', content: data.content, streaming: true }]
        })
      } else if (data.type === 'done') {
        setIsLoading(false)
        setMessages(prev => prev.map(m =>
          m.streaming ? { ...m, streaming: false } : m
        ))
        // Refresh documents and bookings
        if (data.documents_count > 0) fetchDocuments()
        if (data.bookings_count > 0) fetchBookings()
      } else if (data.type === 'error') {
        setIsLoading(false)
        setMessages(prev => [
          ...prev,
          { role: 'agent', content: `**Error:** ${data.content}`, streaming: false }
        ])
      }
    }

    ws.onclose = () => {
      console.log('WebSocket closed')
    }

    return () => ws.close()
  }, [sessionId])

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const fetchDocuments = useCallback(() => {
    if (!sessionId) return
    fetch(`${API_BASE}/api/sessions/${sessionId}/documents`)
      .then(r => r.json())
      .then(data => setDocuments(data.documents || []))
      .catch(() => {})
  }, [sessionId])

  const fetchBookings = useCallback(() => {
    if (!sessionId) return
    fetch(`${API_BASE}/api/sessions/${sessionId}/bookings`)
      .then(r => r.json())
      .then(data => setBookings(data.bookings || []))
      .catch(() => {})
  }, [sessionId])

  const sendMessage = useCallback((text) => {
    const msg = text || input.trim()
    if (!msg || !wsRef.current || isLoading) return

    setMessages(prev => [...prev, { role: 'user', content: msg }])
    wsRef.current.send(JSON.stringify({ message: msg }))
    setInput('')
  }, [input, isLoading])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const totalDocs = documents.length + bookings.length

  return (
    <div className="app-layout">
      <Sidebar
        open={sidebarOpen}
        documents={documents}
        bookings={bookings}
        onDocClick={setSelectedDoc}
      />

      <div className="chat-area">
        <header className="chat-header">
          <div className="chat-header-logo">✈</div>
          <div className="chat-header-info">
            <h1>Voyager Travel</h1>
            <p>Your AI travel agent — flights, hotels, experiences</p>
          </div>
          <button className="toggle-sidebar" onClick={() => setSidebarOpen(!sidebarOpen)}>
            {sidebarOpen ? '✕' : '☰'} Documents
            {totalDocs > 0 && <span className="badge">{totalDocs}</span>}
          </button>
        </header>

        {messages.length === 0 ? (
          <Welcome onSuggestionClick={sendMessage} />
        ) : (
          <Chat
            messages={messages}
            isLoading={isLoading}
            messagesEndRef={messagesEndRef}
          />
        )}

        <div className="input-area">
          <div className="input-wrapper">
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Tell me where you'd like to go..."
              disabled={isLoading || !sessionId}
              rows={1}
            />
            <button
              className="send-btn"
              onClick={() => sendMessage()}
              disabled={!input.trim() || isLoading || !sessionId}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {selectedDoc && (
        <DocumentModal doc={selectedDoc} onClose={() => setSelectedDoc(null)} />
      )}
    </div>
  )
}

function Welcome({ onSuggestionClick }) {
  const suggestions = [
    "Plan a romantic trip to Paris for 2",
    "Find flights from NYC to Tokyo next month",
    "I need a family vacation to Hawaii",
    "Book a business trip to London",
  ]

  return (
    <div className="welcome">
      <div className="welcome-logo">✈</div>
      <h2>Welcome to Voyager Travel</h2>
      <p>
        I'm your AI travel agent! Tell me where you want to go, and I'll find
        the best flights, hotels, and activities. I handle everything from
        search to booking.
      </p>
      <div className="welcome-suggestions">
        {suggestions.map((s, i) => (
          <button key={i} className="suggestion-chip" onClick={() => onSuggestionClick(s)}>
            {s}
          </button>
        ))}
      </div>
    </div>
  )
}
