"""Tests for the FastAPI endpoints."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from flight_booking.api import app


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthEndpoint:
    def test_health(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestSessionEndpoints:
    def test_create_session(self, client):
        with patch("flight_booking.api.TravelAgent"):
            resp = client.post("/api/sessions")
            assert resp.status_code == 200
            data = resp.json()
            assert "session_id" in data
            assert len(data["session_id"]) == 12

    def test_get_documents_invalid_session(self, client):
        resp = client.get("/api/sessions/nonexistent/documents")
        assert resp.status_code == 404

    def test_get_bookings_invalid_session(self, client):
        resp = client.get("/api/sessions/nonexistent/bookings")
        assert resp.status_code == 404
