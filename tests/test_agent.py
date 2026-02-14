"""Tests for the TravelAgent (Claude agentic loop).

These tests mock the Anthropic client so no real API calls are made.
They verify the tool-use loop, message management, and document retrieval.
"""

from __future__ import annotations

import json
import os
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from flight_booking.agent import MODEL, SYSTEM_PROMPT, TravelAgent
from flight_booking.tools import ToolExecutor


class TestTravelAgentInit:
    def test_default_init(self):
        with patch("flight_booking.agent.anthropic"):
            agent = TravelAgent()
            assert agent.messages == []
            assert isinstance(agent.executor, ToolExecutor)

    def test_custom_executor(self):
        with patch("flight_booking.agent.anthropic"):
            ex = MagicMock(spec=ToolExecutor)
            agent = TravelAgent(executor=ex)
            assert agent.executor is ex


class TestSystemPrompt:
    def test_prompt_contains_personality(self):
        assert "Voyager" in SYSTEM_PROMPT
        assert "travel agent" in SYSTEM_PROMPT.lower()

    def test_prompt_forbids_price_disclosure(self):
        assert "NEVER mention markups" in SYSTEM_PROMPT

    def test_prompt_mentions_tools(self):
        assert "resolve_location" in SYSTEM_PROMPT


class TestChatSync:
    def _make_text_response(self, text: str):
        """Create a mock API response with just a text block."""
        block = SimpleNamespace(type="text", text=text)
        block.model_dump = lambda: {"type": "text", "text": text}
        return SimpleNamespace(content=[block], stop_reason="end_turn")

    def _make_tool_then_text(self, tool_name, tool_input, final_text):
        """Create two responses: first with tool_use, second with text."""
        tool_block = SimpleNamespace(
            type="tool_use", id="call_123", name=tool_name, input=tool_input,
        )
        tool_block.model_dump = lambda: {
            "type": "tool_use", "id": "call_123",
            "name": tool_name, "input": tool_input,
        }
        tool_response = SimpleNamespace(content=[tool_block], stop_reason="tool_use")

        text_block = SimpleNamespace(type="text", text=final_text)
        text_block.model_dump = lambda: {"type": "text", "text": final_text}
        text_response = SimpleNamespace(content=[text_block], stop_reason="end_turn")

        return [tool_response, text_response]

    @patch("flight_booking.agent.anthropic")
    def test_simple_text_response(self, mock_anthropic):
        agent = TravelAgent()
        mock_client = MagicMock()
        agent.client = mock_client

        mock_client.messages.create.return_value = self._make_text_response("Hello, traveler!")

        result = agent.chat_sync("Hi")

        assert result == "Hello, traveler!"
        assert len(agent.messages) == 2  # user + assistant
        assert agent.messages[0]["role"] == "user"
        assert agent.messages[1]["role"] == "assistant"

    @patch("flight_booking.agent.anthropic")
    def test_tool_use_loop(self, mock_anthropic):
        executor = MagicMock(spec=ToolExecutor)
        executor.execute.return_value = json.dumps({"locations": [{"iata": "JFK"}]})

        agent = TravelAgent(executor=executor)
        mock_client = MagicMock()
        agent.client = mock_client

        responses = self._make_tool_then_text(
            "resolve_location", {"keyword": "New York"},
            "JFK is John F. Kennedy International Airport!",
        )
        mock_client.messages.create.side_effect = responses

        result = agent.chat_sync("Where is New York?")

        assert "JFK" in result
        executor.execute.assert_called_once_with("resolve_location", {"keyword": "New York"})
        # Messages: user, assistant (tool_use), user (tool_result), assistant (text)
        assert len(agent.messages) == 4

    @patch("flight_booking.agent.anthropic")
    def test_multiple_messages_accumulate(self, mock_anthropic):
        agent = TravelAgent()
        mock_client = MagicMock()
        agent.client = mock_client

        mock_client.messages.create.side_effect = [
            self._make_text_response("Response 1"),
            self._make_text_response("Response 2"),
        ]

        agent.chat_sync("Message 1")
        agent.chat_sync("Message 2")

        assert len(agent.messages) == 4  # 2 user + 2 assistant


class TestGetDocuments:
    @patch("flight_booking.agent.anthropic")
    def test_get_documents_empty(self, mock_anthropic):
        agent = TravelAgent()
        agent.executor.output_dir = "/nonexistent"
        assert agent.get_documents() == []

    @patch("flight_booking.agent.anthropic")
    def test_get_documents_with_files(self, mock_anthropic, tmp_path):
        agent = TravelAgent()
        agent.executor.output_dir = str(tmp_path)

        (tmp_path / "ticket_VYG-001.txt").write_text("ticket content")
        (tmp_path / "voucher_VYG-002.txt").write_text("voucher content")
        (tmp_path / "trip_plan_paris.md").write_text("# Paris Plan")

        docs = agent.get_documents()
        assert len(docs) == 3
        types = {d["type"] for d in docs}
        assert types == {"ticket", "voucher", "presentation"}


class TestGetBookings:
    @patch("flight_booking.agent.anthropic")
    def test_get_bookings_empty(self, mock_anthropic):
        agent = TravelAgent()
        assert agent.get_bookings() == []

    @patch("flight_booking.agent.anthropic")
    def test_get_bookings_exposes_markup_only(self, mock_anthropic):
        from flight_booking.models import BookingRecord
        agent = TravelAgent()
        agent.executor.bookings = [
            BookingRecord(
                booking_id="VYG-F-001", booking_type="flight",
                traveler_name="John", traveler_email="j@x.com",
                markup_price=385.0, actual_price=350.0, currency="USD",
            ),
        ]

        bookings = agent.get_bookings()
        assert len(bookings) == 1
        assert bookings[0]["price"] == 385.0
        assert "actual_price" not in bookings[0]
