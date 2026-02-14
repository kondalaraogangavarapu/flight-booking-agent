import React from 'react'
import ReactMarkdown from 'react-markdown'

export default function Chat({ messages, isLoading, messagesEndRef }) {
  return (
    <div className="messages-container">
      {messages.map((msg, i) => (
        <div key={i} className={`message ${msg.role}`}>
          <div className="message-avatar">
            {msg.role === 'agent' ? '✈' : '👤'}
          </div>
          <div className="message-bubble">
            {msg.role === 'agent' ? (
              <ReactMarkdown>{msg.content}</ReactMarkdown>
            ) : (
              <p>{msg.content}</p>
            )}
          </div>
        </div>
      ))}

      {isLoading && messages[messages.length - 1]?.role !== 'agent' && (
        <div className="message agent">
          <div className="message-avatar">✈</div>
          <div className="message-bubble">
            <div className="typing-indicator">
              <span /><span /><span />
            </div>
          </div>
        </div>
      )}

      <div ref={messagesEndRef} />
    </div>
  )
}
