import React, { useState } from 'react'

export default function Sidebar({ open, documents, bookings, onDocClick }) {
  const [tab, setTab] = useState('documents')

  return (
    <div className={`sidebar ${open ? '' : 'collapsed'}`}>
      <div className="sidebar-header">
        <span style={{ fontSize: 20 }}>📋</span>
        <h2>Trip Details</h2>
      </div>

      <div className="sidebar-tabs">
        <button
          className={`sidebar-tab ${tab === 'documents' ? 'active' : ''}`}
          onClick={() => setTab('documents')}
        >
          Documents {documents.length > 0 && `(${documents.length})`}
        </button>
        <button
          className={`sidebar-tab ${tab === 'bookings' ? 'active' : ''}`}
          onClick={() => setTab('bookings')}
        >
          Bookings {bookings.length > 0 && `(${bookings.length})`}
        </button>
      </div>

      <div className="sidebar-content">
        {tab === 'documents' && (
          documents.length === 0 ? (
            <div className="sidebar-empty">
              <div style={{ fontSize: 32, marginBottom: 8 }}>📄</div>
              <p>No documents yet. Your tickets, vouchers, and trip plans will appear here.</p>
            </div>
          ) : (
            documents.map((doc, i) => (
              <div key={i} className="doc-card" onClick={() => onDocClick(doc)}>
                <div className="doc-card-header">
                  <span className={`doc-card-type ${doc.type}`}>{doc.type}</span>
                </div>
                <div className="doc-card-name">{doc.filename}</div>
              </div>
            ))
          )
        )}

        {tab === 'bookings' && (
          bookings.length === 0 ? (
            <div className="sidebar-empty">
              <div style={{ fontSize: 32, marginBottom: 8 }}>🎫</div>
              <p>No bookings yet. Book flights and hotels through the chat.</p>
            </div>
          ) : (
            bookings.map((b, i) => (
              <div key={i} className="booking-card">
                <div className="booking-card-header">
                  <span className="booking-id">{b.booking_id}</span>
                  <span className="booking-price">
                    ${b.price?.toFixed(2)} {b.currency}
                  </span>
                </div>
                <div className="booking-detail">
                  <strong>{b.type === 'flight' ? '✈ Flight' : '🏨 Hotel'}</strong>
                </div>
                <div className="booking-detail">{b.traveler}</div>
                {b.details && (
                  <div className="booking-detail" style={{ marginTop: 4, fontSize: 12 }}>
                    {b.type === 'flight'
                      ? `${b.details.origin} → ${b.details.destination} (${b.details.airline})`
                      : `${b.details.hotel_name} · ${b.details.check_in} to ${b.details.check_out}`
                    }
                  </div>
                )}
              </div>
            ))
          )
        )}
      </div>
    </div>
  )
}
