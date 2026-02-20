"""Conversational flight-booking agent powered by an LLM.

The agent interprets natural-language requests and maps them to
flight search / booking actions.  When no LLM API key is configured
it falls back to simple keyword matching so the service can still
run in demo mode.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta

from app.config import settings
from app.flights import search_flights
from app.models import AgentResponse

logger = logging.getLogger(__name__)


def _parse_with_keywords(message: str) -> AgentResponse:
    """Lightweight keyword-based fallback when no LLM is available."""
    lower = message.lower()
    actions: list[str] = []

    if any(kw in lower for kw in ("search", "find", "look", "flight")):
        # Try to extract origin/destination from the message
        words = message.upper().split()
        iata_codes = [w for w in words if len(w) == 3 and w.isalpha()]

        if len(iata_codes) >= 2:
            origin, destination = iata_codes[0], iata_codes[1]
            departure_date = (date.today() + timedelta(days=7)).strftime("%Y-%m-%d")
            results = search_flights(origin, destination, departure_date)
            actions.append(f"searched flights {origin} -> {destination}")
            if results:
                flights_text = "\n".join(
                    f"  - {f.airline} {f.flight_id}: {f.departure:%H:%M}-{f.arrival:%H:%M} ${f.price}"
                    for f in results
                )
                return AgentResponse(
                    reply=f"I found {len(results)} flight(s) from {origin} to {destination}:\n{flights_text}",
                    actions_taken=actions,
                )
            return AgentResponse(
                reply=f"Sorry, I couldn't find any flights from {origin} to {destination} on {departure_date}.",
                actions_taken=actions,
            )

        return AgentResponse(
            reply="I can help you search for flights! Please provide origin and destination airport codes (e.g., 'Search flights JFK LAX').",
            actions_taken=actions,
        )

    if any(kw in lower for kw in ("book", "reserve")):
        return AgentResponse(
            reply="To book a flight, please first search for available flights, then use the /api/v1/bookings endpoint with the flight ID.",
            actions_taken=["provided booking instructions"],
        )

    if any(kw in lower for kw in ("status", "booking")):
        return AgentResponse(
            reply="To check a booking, use the /api/v1/bookings/{booking_id} endpoint with your booking reference.",
            actions_taken=["provided status check instructions"],
        )

    return AgentResponse(
        reply=(
            "Hello! I'm your flight booking assistant. I can help you:\n"
            "  - Search for flights (e.g., 'Find flights from JFK to LAX')\n"
            "  - Book flights\n"
            "  - Check booking status\n"
            "How can I help you today?"
        ),
        actions_taken=[],
    )


def handle_message(message: str) -> AgentResponse:
    """Process a user message and return an agent response."""
    if not settings.ANTHROPIC_API_KEY:
        logger.info("No ANTHROPIC_API_KEY set; using keyword fallback.")
        return _parse_with_keywords(message)

    # When an API key is available, delegate to the LLM.
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

        system_prompt = (
            "You are a helpful flight booking assistant. "
            "Help the user search for flights and make bookings. "
            "Available routes for demo: JFK-LAX, LAX-JFK, JFK-LHR, SFO-NRT. "
            "When the user wants to search, extract origin, destination, and date. "
            "Respond concisely."
        )

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=512,
            system=system_prompt,
            messages=[{"role": "user", "content": message}],
        )

        reply_text = response.content[0].text
        return AgentResponse(reply=reply_text, actions_taken=["llm_response"])

    except ImportError:
        logger.exception("Failed to import anthropic SDK; falling back to keyword parser.")
        return _parse_with_keywords(message)
    except anthropic.APIConnectionError:
        logger.exception("Could not connect to Anthropic API; falling back to keyword parser.")
        return _parse_with_keywords(message)
    except anthropic.APIStatusError:
        logger.exception("Anthropic API returned an error; falling back to keyword parser.")
        return _parse_with_keywords(message)
