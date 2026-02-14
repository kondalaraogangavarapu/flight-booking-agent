import React from 'react'
import ReactMarkdown from 'react-markdown'

export default function DocumentModal({ doc, onClose }) {
  if (!doc) return null

  const isMarkdown = doc.filename.endsWith('.md')

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>
            <span className={`doc-card-type ${doc.type}`} style={{ marginRight: 8 }}>
              {doc.type}
            </span>
            {doc.filename}
          </h3>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        <div className="modal-body">
          {isMarkdown ? (
            <div className="markdown-content">
              <ReactMarkdown>{doc.content}</ReactMarkdown>
            </div>
          ) : (
            <pre>{doc.content}</pre>
          )}
        </div>
      </div>
    </div>
  )
}
