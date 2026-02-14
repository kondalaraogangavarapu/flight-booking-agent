"""Tool definitions and implementations for the travel agent.

Every price returned to the Claude agent has a 10% markup applied.
The actual (cost) price is tracked internally for profit calculation
but never exposed to the traveler.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from typing import Any

from .amadeus_client import AmadeusFlightClient, FlightSearchError
from .models import Activity, BookingRecord, Flight, HotelOffer, PointOfInterest
from .receipts import generate_flight_ticket, generate_hotel_voucher
from .presentations import generate_trip_presentation

MARKUP = 0.10  # 10% markup


def _markup(price: float) -> float:
    """Apply 10% markup and round to 2 decimals."""
    return round(price * (1 + MARKUP), 2)


# ---------------------------------------------------------------------------
# Tool schema definitions (sent to Claude)
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "search_flights",
        "description": (
            "Search for available flights between two cities. "
            "Returns a list of flights with prices, airlines, times, and stops."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "origin": {"type": "string", "description": "Departure airport IATA code (e.g., 'JFK')"},
                "destination": {"type": "string", "description": "Arrival airport IATA code (e.g., 'LAX')"},
                "departure_date": {"type": "string", "description": "Departure date YYYY-MM-DD"},
                "return_date": {"type": "string", "description": "Return date YYYY-MM-DD (omit for one-way)"},
                "passengers": {"type": "integer", "description": "Number of adult passengers", "default": 1},
                "cabin_class": {
                    "type": "string",
                    "description": "Cabin class",
                    "enum": ["ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"],
                    "default": "ECONOMY",
                },
                "non_stop": {"type": "boolean", "description": "Only show non-stop flights", "default": False},
                "max_price": {"type": "number", "description": "Maximum price per person in USD"},
            },
            "required": ["origin", "destination", "departure_date"],
        },
    },
    {
        "name": "search_hotels",
        "description": (
            "Search for hotel rooms in a city. "
            "Returns available hotels with room types, prices per night, and total prices."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "city_code": {"type": "string", "description": "IATA city code (e.g., 'PAR', 'NYC', 'LON')"},
                "check_in": {"type": "string", "description": "Check-in date YYYY-MM-DD"},
                "check_out": {"type": "string", "description": "Check-out date YYYY-MM-DD"},
                "guests": {"type": "integer", "description": "Number of guests", "default": 1},
                "rooms": {"type": "integer", "description": "Number of rooms", "default": 1},
            },
            "required": ["city_code", "check_in", "check_out"],
        },
    },
    {
        "name": "search_activities",
        "description": (
            "Search for bookable tours, activities, and experiences at a destination. "
            "Returns activities with descriptions, prices, and ratings."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "city_code": {"type": "string", "description": "IATA city code to search near"},
            },
            "required": ["city_code"],
        },
    },
    {
        "name": "search_points_of_interest",
        "description": (
            "Search for popular attractions, landmarks, restaurants, and things to see. "
            "Returns points of interest with categories and tags."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "city_code": {"type": "string", "description": "IATA city code to search near"},
                "categories": {
                    "type": "string",
                    "description": "Comma-separated categories to filter by",
                    "enum": ["SIGHTS", "BEACH_PARK", "HISTORICAL", "NIGHTLIFE", "RESTAURANT", "SHOPPING"],
                },
            },
            "required": ["city_code"],
        },
    },
    {
        "name": "resolve_location",
        "description": (
            "Look up an airport or city by name and return matching IATA codes. "
            "Use this when the traveler gives a city name instead of a code."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "City name or airport name to search"},
            },
            "required": ["keyword"],
        },
    },
    {
        "name": "book_flight",
        "description": (
            "Book a flight for a traveler. Requires a flight from search results. "
            "Returns a booking confirmation and generates a ticket."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "flight_index": {"type": "integer", "description": "Index of the flight from the last search results (0-based)"},
                "traveler_name": {"type": "string", "description": "Full name of the primary traveler"},
                "traveler_email": {"type": "string", "description": "Email address for confirmation"},
            },
            "required": ["flight_index", "traveler_name", "traveler_email"],
        },
    },
    {
        "name": "book_hotel",
        "description": (
            "Book a hotel room for a traveler. Requires a hotel from search results. "
            "Returns a booking confirmation and generates a voucher."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "hotel_index": {"type": "integer", "description": "Index of the hotel from the last search results (0-based)"},
                "traveler_name": {"type": "string", "description": "Full name of the guest"},
                "traveler_email": {"type": "string", "description": "Email address for confirmation"},
            },
            "required": ["hotel_index", "traveler_name", "traveler_email"],
        },
    },
    {
        "name": "create_trip_presentation",
        "description": (
            "Generate a beautiful trip presentation/plan document for the traveler. "
            "Summarizes the full trip including flights, hotels, activities, and a "
            "day-by-day itinerary. Saves a presentation file the traveler can keep."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "trip_title": {"type": "string", "description": "A catchy title for the trip (e.g., 'Parisian Adventure')"},
                "traveler_name": {"type": "string", "description": "Traveler's name"},
                "destination": {"type": "string", "description": "Destination city name"},
                "departure_date": {"type": "string", "description": "Trip start date YYYY-MM-DD"},
                "return_date": {"type": "string", "description": "Trip end date YYYY-MM-DD"},
                "travelers_count": {"type": "integer", "description": "Number of travelers"},
                "trip_vibe": {"type": "string", "description": "Trip mood/style (e.g., 'romantic', 'adventure', 'family')"},
                "notes": {"type": "string", "description": "Any additional notes or highlights to include"},
            },
            "required": ["trip_title", "traveler_name", "destination", "departure_date", "return_date"],
        },
    },
]


# ---------------------------------------------------------------------------
# Tool executor
# ---------------------------------------------------------------------------

class ToolExecutor:
    """Executes tools, manages state, applies markup, generates documents."""

    def __init__(self, client: AmadeusFlightClient | None = None) -> None:
        self.client = client or AmadeusFlightClient()
        # State: last search results (for booking by index)
        self.last_flights: list[Flight] = []
        self.last_hotels: list[HotelOffer] = []
        self.last_activities: list[Activity] = []
        self.last_pois: list[PointOfInterest] = []
        # Booking records (internal)
        self.bookings: list[BookingRecord] = []
        # Output directory for receipts and presentations
        self.output_dir = os.path.join(os.getcwd(), "trip_documents")
        os.makedirs(self.output_dir, exist_ok=True)

    def execute(self, tool_name: str, tool_input: dict[str, Any]) -> str:
        """Dispatch to the right tool and return a JSON string result."""
        dispatch = {
            "search_flights": self._search_flights,
            "search_hotels": self._search_hotels,
            "search_activities": self._search_activities,
            "search_points_of_interest": self._search_pois,
            "resolve_location": self._resolve_location,
            "book_flight": self._book_flight,
            "book_hotel": self._book_hotel,
            "create_trip_presentation": self._create_presentation,
        }
        handler = dispatch.get(tool_name)
        if not handler:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
        try:
            result = handler(tool_input)
            return json.dumps(result, default=str)
        except FlightSearchError as e:
            return json.dumps({"error": str(e)})
        except Exception as e:
            return json.dumps({"error": f"Tool failed: {e}"})

    # --- Search tools ---

    def _search_flights(self, inp: dict) -> dict:
        raw_flights = self.client.search_flights(
            origin=inp["origin"],
            destination=inp["destination"],
            departure_date=inp["departure_date"],
            return_date=inp.get("return_date"),
            passengers=inp.get("passengers", 1),
            cabin_class=inp.get("cabin_class", "ECONOMY"),
            max_price=inp.get("max_price"),
            non_stop=inp.get("non_stop", False),
        )

        self.last_flights = []
        results = []
        for i, f in enumerate(raw_flights):
            actual = f.price
            marked = _markup(actual)
            flight = Flight(
                flight_number=f.flight_number,
                airline=f.airline,
                origin=f.origin,
                destination=f.destination,
                departure=f.departure.isoformat(),
                arrival=f.arrival.isoformat(),
                duration=f.duration_display(),
                stops=f.stops,
                cabin_class=f.cabin_class,
                actual_price=actual,
                markup_price=marked,
                currency=f.currency,
                seats_left=f.available_seats,
                raw_offer=f.raw_offer,
            )
            self.last_flights.append(flight)
            results.append({
                "index": i,
                "flight_number": flight.flight_number,
                "airline": flight.airline,
                "origin": flight.origin,
                "destination": flight.destination,
                "departure": flight.departure,
                "arrival": flight.arrival,
                "duration": flight.duration,
                "stops": flight.stops,
                "cabin_class": flight.cabin_class,
                "price": flight.markup_price,
                "currency": flight.currency,
                "seats_left": flight.seats_left,
            })

        return {"flights": results, "count": len(results)}

    def _search_hotels(self, inp: dict) -> dict:
        city_code = inp["city_code"]
        check_in = inp["check_in"]
        check_out = inp["check_out"]
        guests = inp.get("guests", 1)
        rooms = inp.get("rooms", 1)

        hotels = self.client.search_hotels_by_city(city_code)
        if not hotels:
            return {"hotels": [], "count": 0}

        hotel_ids = [h.hotel_id for h in hotels[:10]]
        offers = self.client.search_hotel_offers(hotel_ids, check_in, check_out, guests, rooms)

        self.last_hotels = []
        results = []
        for i, o in enumerate(offers):
            actual = o.price
            marked = _markup(actual)
            ci = datetime.strptime(o.check_in, "%Y-%m-%d")
            co = datetime.strptime(o.check_out, "%Y-%m-%d")
            nights = max((co - ci).days, 1)

            hotel = HotelOffer(
                hotel_name=o.hotel.name,
                hotel_id=o.hotel.hotel_id,
                offer_id=o.offer_id,
                room_type=o.room_type,
                room_description=o.room_description,
                board_type=o.board_type,
                check_in=o.check_in,
                check_out=o.check_out,
                nights=nights,
                actual_price=actual,
                markup_price=marked,
                currency=o.currency,
                cancellation_info=o.cancellation_info,
                raw_offer=o.raw_offer,
            )
            self.last_hotels.append(hotel)
            results.append({
                "index": i,
                "hotel_name": hotel.hotel_name,
                "room_type": hotel.room_type,
                "room_description": hotel.room_description,
                "board_type": hotel.board_type,
                "check_in": hotel.check_in,
                "check_out": hotel.check_out,
                "nights": hotel.nights,
                "total_price": hotel.markup_price,
                "price_per_night": round(hotel.markup_price / nights, 2),
                "currency": hotel.currency,
                "cancellation": hotel.cancellation_info,
            })

        return {"hotels": results, "count": len(results)}

    def _search_activities(self, inp: dict) -> dict:
        coords = self.client.get_city_coordinates(inp["city_code"])
        if not coords:
            return {"activities": [], "count": 0}

        raw = self.client.search_activities(coords[0], coords[1])
        self.last_activities = []
        results = []
        for i, a in enumerate(raw):
            actual = a.price
            marked = _markup(actual) if actual > 0 else 0
            act = Activity(
                name=a.name, description=a.description,
                actual_price=actual, markup_price=marked,
                currency=a.currency, rating=a.rating, booking_link=a.booking_link,
            )
            self.last_activities.append(act)
            results.append({
                "index": i, "name": act.name, "description": act.description,
                "price": act.markup_price, "currency": act.currency,
                "rating": act.rating,
            })

        return {"activities": results, "count": len(results)}

    def _search_pois(self, inp: dict) -> dict:
        coords = self.client.get_city_coordinates(inp["city_code"])
        if not coords:
            return {"points_of_interest": [], "count": 0}

        categories = inp.get("categories", "")
        raw = self.client.search_pois(coords[0], coords[1], categories)
        self.last_pois = []
        results = []
        for p in raw:
            poi = PointOfInterest(name=p.name, category=p.category, tags=p.tags)
            self.last_pois.append(poi)
            results.append({"name": poi.name, "category": poi.category, "tags": poi.tags})

        return {"points_of_interest": results, "count": len(results)}

    def _resolve_location(self, inp: dict) -> dict:
        locations = self.client.search_locations(inp["keyword"])
        return {"locations": locations[:5]}

    # --- Booking tools ---

    def _book_flight(self, inp: dict) -> dict:
        idx = inp["flight_index"]
        if idx < 0 or idx >= len(self.last_flights):
            return {"error": f"Invalid flight index {idx}. Search for flights first."}

        flight = self.last_flights[idx]
        name = inp["traveler_name"]
        email = inp["traveler_email"]

        booking_id = f"VYG-F-{uuid.uuid4().hex[:6].upper()}"
        now = datetime.now().isoformat()

        # Try real API booking
        api_id = None
        try:
            if flight.raw_offer:
                result = self.client.create_flight_booking(flight.raw_offer, name, email)
                api_id = result.get("id")
        except Exception:
            pass

        record = BookingRecord(
            booking_id=api_id or booking_id,
            booking_type="flight",
            traveler_name=name,
            traveler_email=email,
            details={
                "flight_number": flight.flight_number,
                "airline": flight.airline,
                "origin": flight.origin,
                "destination": flight.destination,
                "departure": flight.departure,
                "arrival": flight.arrival,
                "cabin_class": flight.cabin_class,
            },
            markup_price=flight.markup_price,
            actual_price=flight.actual_price,
            currency=flight.currency,
            timestamp=now,
        )
        self.bookings.append(record)

        # Generate ticket
        ticket_path = os.path.join(self.output_dir, f"ticket_{record.booking_id}.txt")
        ticket_content = generate_flight_ticket(record)
        with open(ticket_path, "w") as f:
            f.write(ticket_content)

        return {
            "status": "confirmed",
            "booking_id": record.booking_id,
            "flight": flight.flight_number,
            "airline": flight.airline,
            "route": f"{flight.origin} -> {flight.destination}",
            "departure": flight.departure,
            "price": flight.markup_price,
            "currency": flight.currency,
            "traveler": name,
            "ticket_file": ticket_path,
            "message": f"Flight booked! Ticket saved to {ticket_path}",
        }

    def _book_hotel(self, inp: dict) -> dict:
        idx = inp["hotel_index"]
        if idx < 0 or idx >= len(self.last_hotels):
            return {"error": f"Invalid hotel index {idx}. Search for hotels first."}

        hotel = self.last_hotels[idx]
        name = inp["traveler_name"]
        email = inp["traveler_email"]

        booking_id = f"VYG-H-{uuid.uuid4().hex[:6].upper()}"
        now = datetime.now().isoformat()

        record = BookingRecord(
            booking_id=booking_id,
            booking_type="hotel",
            traveler_name=name,
            traveler_email=email,
            details={
                "hotel_name": hotel.hotel_name,
                "room_type": hotel.room_type,
                "room_description": hotel.room_description,
                "check_in": hotel.check_in,
                "check_out": hotel.check_out,
                "nights": hotel.nights,
            },
            markup_price=hotel.markup_price,
            actual_price=hotel.actual_price,
            currency=hotel.currency,
            timestamp=now,
        )
        self.bookings.append(record)

        # Generate voucher
        voucher_path = os.path.join(self.output_dir, f"voucher_{record.booking_id}.txt")
        voucher_content = generate_hotel_voucher(record)
        with open(voucher_path, "w") as f:
            f.write(voucher_content)

        return {
            "status": "confirmed",
            "booking_id": record.booking_id,
            "hotel": hotel.hotel_name,
            "room": hotel.room_type,
            "check_in": hotel.check_in,
            "check_out": hotel.check_out,
            "nights": hotel.nights,
            "price": hotel.markup_price,
            "currency": hotel.currency,
            "traveler": name,
            "voucher_file": voucher_path,
            "message": f"Hotel booked! Voucher saved to {voucher_path}",
        }

    # --- Presentation ---

    def _create_presentation(self, inp: dict) -> dict:
        pres_path = os.path.join(
            self.output_dir,
            f"trip_plan_{inp['destination'].replace(' ', '_').lower()}.md",
        )
        content = generate_trip_presentation(
            title=inp["trip_title"],
            traveler_name=inp["traveler_name"],
            destination=inp["destination"],
            departure_date=inp["departure_date"],
            return_date=inp["return_date"],
            travelers_count=inp.get("travelers_count", 1),
            trip_vibe=inp.get("trip_vibe", ""),
            notes=inp.get("notes", ""),
            flights=self.last_flights,
            hotels=self.last_hotels,
            activities=self.last_activities,
            pois=self.last_pois,
            bookings=self.bookings,
        )
        with open(pres_path, "w") as f:
            f.write(content)

        return {
            "presentation_file": pres_path,
            "message": f"Trip presentation saved to {pres_path}",
        }
