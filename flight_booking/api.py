"""FastAPI backend for the Voyager travel agent.

Provides:
- WebSocket /ws/chat  — real-time streaming chat with the agent
- GET /api/documents  — list generated tickets, vouchers, presentations
- GET /api/bookings   — list bookings (markup prices only)
- Static file serving for the React frontend (production build)
"""

from __future__ import annotations

import asyncio
import json
import os
import uuid
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .agent import TravelAgent
from .tools import ToolExecutor

app = FastAPI(title="Voyager Travel Agent", version="1.0.0")

# CORS for local dev (Vite runs on port 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Per-session agents  (session_id -> TravelAgent)
_sessions: dict[str, TravelAgent] = {}


def _get_or_create_agent(session_id: str) -> TravelAgent:
    if session_id not in _sessions:
        _sessions[session_id] = TravelAgent()
    return _sessions[session_id]


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------

@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/sessions")
async def create_session():
    sid = uuid.uuid4().hex[:12]
    _sessions[sid] = TravelAgent()
    return {"session_id": sid}


@app.get("/api/sessions/{session_id}/documents")
async def get_documents(session_id: str):
    agent = _sessions.get(session_id)
    if not agent:
        return JSONResponse({"error": "Session not found"}, status_code=404)
    return {"documents": agent.get_documents()}


@app.get("/api/sessions/{session_id}/bookings")
async def get_bookings(session_id: str):
    agent = _sessions.get(session_id)
    if not agent:
        return JSONResponse({"error": "Session not found"}, status_code=404)
    return {"bookings": agent.get_bookings()}


# ---------------------------------------------------------------------------
# WebSocket chat — streams agent responses token-by-token
# ---------------------------------------------------------------------------

@app.websocket("/ws/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    await websocket.accept()
    agent = _get_or_create_agent(session_id)

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            user_text = msg.get("message", "")

            if not user_text:
                await websocket.send_json({"type": "error", "content": "Empty message"})
                continue

            # Signal start
            await websocket.send_json({"type": "start"})

            try:
                # Run the streaming chat in a thread so we don't block the event loop
                # (the anthropic SDK uses synchronous HTTP under the hood for streaming)
                full_response = await asyncio.to_thread(agent.chat_sync, user_text)

                # Send the full response (client renders markdown)
                await websocket.send_json({
                    "type": "chunk",
                    "content": full_response,
                })
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "content": f"Agent error: {e}",
                })

            # Signal done + send updated document/booking counts
            await websocket.send_json({
                "type": "done",
                "documents_count": len(agent.get_documents()),
                "bookings_count": len(agent.get_bookings()),
            })

    except WebSocketDisconnect:
        pass


# ---------------------------------------------------------------------------
# Serve React frontend (production build)
# ---------------------------------------------------------------------------

_frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(_frontend_dir):
    app.mount("/", StaticFiles(directory=_frontend_dir, html=True), name="frontend")
