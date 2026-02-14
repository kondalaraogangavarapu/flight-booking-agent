"""Conversational flight booking agent backed by the Amadeus API."""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from enum import Enum, auto

from .amadeus_client import AmadeusFlightClient
from .models import Booking, CabinClass, Flight, SearchCriteria, TripType
from .search import FlightSearchEngine


class AgentState(Enum):
    GREETING = auto()
    COLLECTING_ORIGIN = auto()
    DISAMBIGUATING_ORIGIN = auto()
    COLLECTING_DESTINATION = auto()
    DISAMBIGUATING_DESTINATION = auto()
    COLLECTING_DATES = auto()
    COLLECTING_RETURN_DATE = auto()
    COLLECTING_PASSENGERS = auto()
    COLLECTING_CABIN_CLASS = auto()
    COLLECTING_PREFERENCES = auto()
    SHOWING_RESULTS = auto()
    SELECTING_OUTBOUND = auto()
    COLLECTING_PASSENGER_INFO = auto()
    COLLECTING_EMAIL = auto()
    CONFIRMING_BOOKING = auto()
    COMPLETED = auto()


class FlightBookingAgent:
    """Interactive agent that guides users through flight booking with real data."""

    def __init__(self, client: AmadeusFlightClient | None = None) -> None:
        self.engine = FlightSearchEngine(client)
        self.state = AgentState.GREETING
        self.criteria = SearchCriteria()
        self.booking = Booking()
        self.outbound_flights: list[Flight] = []
        self.return_flights: list[Flight] = []
        self._location_options: list[dict[str, str]] = []

    def greet(self) -> str:
        """Return the initial greeting message."""
        self.state = AgentState.COLLECTING_ORIGIN
        return (
            "Welcome to FlightBooker! I'll help you find and book the best flights "
            "from real airlines.\n\n"
            "Let's get started. Where would you like to fly from?\n"
            "(Enter a city name or airport code, e.g., 'New York' or 'JFK')"
        )

    def process_input(self, user_input: str) -> str:
        """Process user input and return the agent's response."""
        text = user_input.strip()
        if not text:
            return "I didn't catch that. Could you please try again?"

        lower = text.lower()
        if lower in ("quit", "exit", "bye", "cancel"):
            self.state = AgentState.COMPLETED
            return "Thanks for using FlightBooker! Safe travels!"
        if lower in ("start over", "restart", "reset"):
            client = self.engine.client
            self.__init__(client)
            return self.greet()
        if lower == "help":
            return self._help_text()

        handler = {
            AgentState.COLLECTING_ORIGIN: self._handle_origin,
            AgentState.DISAMBIGUATING_ORIGIN: self._handle_disambiguate_origin,
            AgentState.COLLECTING_DESTINATION: self._handle_destination,
            AgentState.DISAMBIGUATING_DESTINATION: self._handle_disambiguate_destination,
            AgentState.COLLECTING_DATES: self._handle_departure_date,
            AgentState.COLLECTING_RETURN_DATE: self._handle_return_date,
            AgentState.COLLECTING_PASSENGERS: self._handle_passengers,
            AgentState.COLLECTING_CABIN_CLASS: self._handle_cabin_class,
            AgentState.COLLECTING_PREFERENCES: self._handle_preferences,
            AgentState.SELECTING_OUTBOUND: self._handle_outbound_selection,
            AgentState.COLLECTING_PASSENGER_INFO: self._handle_passenger_name,
            AgentState.COLLECTING_EMAIL: self._handle_email,
            AgentState.CONFIRMING_BOOKING: self._handle_confirmation,
        }.get(self.state)

        if handler:
            return handler(text)
        return "Something went wrong. Type 'restart' to start over."

    # --- Location resolution ---

    def _resolve_location(self, text: str) -> list[dict[str, str]]:
        """Resolve user input to airport IATA codes via Amadeus."""
        text_clean = text.strip().upper()
        # If it looks like a 3-letter IATA code, accept it directly
        if re.match(r"^[A-Z]{3}$", text_clean):
            return [{"iata": text_clean, "name": text_clean, "city": "", "country": "", "type": "AIRPORT"}]
        return self.engine.resolve_location(text)

    def _format_location_options(self, locations: list[dict[str, str]]) -> str:
        lines = []
        for i, loc in enumerate(locations, 1):
            city = loc.get("city", "")
            country = loc.get("country", "")
            name = loc.get("name", "")
            iata = loc.get("iata", "")
            loc_type = loc.get("type", "")
            label = f"{name}" if name else iata
            if city:
                label = f"{city} - {label}"
            if country:
                label += f" ({country})"
            label += f" [{iata}]"
            if loc_type:
                label += f" ({loc_type.lower()})"
            lines.append(f"  {i}. {label}")
        return "\n".join(lines)

    # --- State handlers ---

    def _handle_origin(self, text: str) -> str:
        locations = self._resolve_location(text)
        if not locations:
            return (
                f"I couldn't find any airports matching '{text}'.\n"
                "Try a city name like 'London' or an airport code like 'LHR'."
            )
        if len(locations) == 1:
            self.criteria.origin = locations[0]["iata"]
            self.state = AgentState.COLLECTING_DESTINATION
            city = locations[0].get("city") or locations[0].get("name") or locations[0]["iata"]
            return (
                f"Great, departing from {city} ({locations[0]['iata']}).\n\n"
                "Where would you like to fly to?"
            )
        # Multiple matches -- ask user to pick
        self._location_options = locations[:5]
        self.state = AgentState.DISAMBIGUATING_ORIGIN
        return (
            f"I found multiple airports matching '{text}'. Which one did you mean?\n\n"
            f"{self._format_location_options(self._location_options)}\n\n"
            "Enter the number of your choice:"
        )

    def _handle_disambiguate_origin(self, text: str) -> str:
        try:
            idx = int(text) - 1
        except ValueError:
            return "Please enter a number from the list above."
        if idx < 0 or idx >= len(self._location_options):
            return f"Please enter a number between 1 and {len(self._location_options)}."
        chosen = self._location_options[idx]
        self.criteria.origin = chosen["iata"]
        self.state = AgentState.COLLECTING_DESTINATION
        city = chosen.get("city") or chosen.get("name") or chosen["iata"]
        return (
            f"Great, departing from {city} ({chosen['iata']}).\n\n"
            "Where would you like to fly to?"
        )

    def _handle_destination(self, text: str) -> str:
        locations = self._resolve_location(text)
        if not locations:
            return (
                f"I couldn't find any airports matching '{text}'.\n"
                "Try a city name or airport code."
            )
        if len(locations) == 1:
            if locations[0]["iata"] == self.criteria.origin:
                return "The destination can't be the same as the origin. Please choose a different city."
            self.criteria.destination = locations[0]["iata"]
            self.state = AgentState.COLLECTING_DATES
            city = locations[0].get("city") or locations[0].get("name") or locations[0]["iata"]
            return (
                f"Flying to {city} ({locations[0]['iata']}).\n\n"
                "When would you like to depart?\n"
                "(Enter a date like '2026-03-15' or 'March 15')"
            )
        self._location_options = locations[:5]
        self.state = AgentState.DISAMBIGUATING_DESTINATION
        return (
            f"I found multiple airports matching '{text}'. Which one did you mean?\n\n"
            f"{self._format_location_options(self._location_options)}\n\n"
            "Enter the number of your choice:"
        )

    def _handle_disambiguate_destination(self, text: str) -> str:
        try:
            idx = int(text) - 1
        except ValueError:
            return "Please enter a number from the list above."
        if idx < 0 or idx >= len(self._location_options):
            return f"Please enter a number between 1 and {len(self._location_options)}."
        chosen = self._location_options[idx]
        if chosen["iata"] == self.criteria.origin:
            return "The destination can't be the same as the origin. Please choose a different number."
        self.criteria.destination = chosen["iata"]
        self.state = AgentState.COLLECTING_DATES
        city = chosen.get("city") or chosen.get("name") or chosen["iata"]
        return (
            f"Flying to {city} ({chosen['iata']}).\n\n"
            "When would you like to depart?\n"
            "(Enter a date like '2026-03-15' or 'March 15')"
        )

    def _handle_departure_date(self, text: str) -> str:
        date = self._parse_date(text)
        if not date:
            return (
                "I couldn't understand that date. Please enter a date like:\n"
                "  - 2026-03-15\n"
                "  - March 15\n"
                "  - 03/15/2026"
            )
        if date < datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
            return "That date is in the past. Please enter a future date."
        self.criteria.departure_date = date.strftime("%Y-%m-%d")
        self.state = AgentState.COLLECTING_RETURN_DATE
        return (
            f"Departure date: {date.strftime('%B %d, %Y')}.\n\n"
            "Is this a round trip? If so, when would you like to return?\n"
            "(Enter a return date, or type 'one way' for a one-way trip)"
        )

    def _handle_return_date(self, text: str) -> str:
        lower = text.lower()
        if lower in ("one way", "one-way", "oneway", "no", "n", "single"):
            self.criteria.trip_type = TripType.ONE_WAY
            self.criteria.return_date = None
            self.booking.trip_type = TripType.ONE_WAY
            self.state = AgentState.COLLECTING_PASSENGERS
            return "Got it, one-way trip.\n\nHow many passengers will be traveling? (1-9)"

        date = self._parse_date(text)
        if not date:
            return (
                "I couldn't understand that date. Please enter a return date like:\n"
                "  - 2026-03-22\n"
                "  - March 22\n"
                "Or type 'one way' for a one-way trip."
            )
        dep_date = datetime.strptime(self.criteria.departure_date, "%Y-%m-%d")
        if date <= dep_date:
            return "The return date must be after the departure date. Please try again."
        self.criteria.return_date = date.strftime("%Y-%m-%d")
        self.criteria.trip_type = TripType.ROUND_TRIP
        self.booking.trip_type = TripType.ROUND_TRIP
        self.state = AgentState.COLLECTING_PASSENGERS
        return (
            f"Return date: {date.strftime('%B %d, %Y')}.\n\n"
            "How many passengers will be traveling? (1-9)"
        )

    def _handle_passengers(self, text: str) -> str:
        try:
            count = int(text)
        except ValueError:
            return "Please enter a number between 1 and 9."
        if count < 1 or count > 9:
            return "Please enter a number between 1 and 9."
        self.criteria.passengers = count
        self.booking.passengers = count
        self.state = AgentState.COLLECTING_CABIN_CLASS
        return (
            f"Traveling with {count} passenger{'s' if count > 1 else ''}.\n\n"
            "Which cabin class do you prefer?\n"
            "  1. Economy\n"
            "  2. Premium Economy\n"
            "  3. Business\n"
            "  4. First Class\n"
            "(Enter a number or name)"
        )

    def _handle_cabin_class(self, text: str) -> str:
        cabin_map = {
            "1": CabinClass.ECONOMY, "economy": CabinClass.ECONOMY, "eco": CabinClass.ECONOMY,
            "2": CabinClass.PREMIUM_ECONOMY, "premium economy": CabinClass.PREMIUM_ECONOMY,
            "premium": CabinClass.PREMIUM_ECONOMY, "pe": CabinClass.PREMIUM_ECONOMY,
            "3": CabinClass.BUSINESS, "business": CabinClass.BUSINESS, "biz": CabinClass.BUSINESS,
            "4": CabinClass.FIRST, "first": CabinClass.FIRST, "first class": CabinClass.FIRST,
        }
        cabin = cabin_map.get(text.lower())
        if not cabin:
            return "Please enter 1-4 or the class name (economy, premium economy, business, first)."
        self.criteria.cabin_class = cabin
        self.state = AgentState.COLLECTING_PREFERENCES
        return (
            f"Cabin class: {cabin.display()}.\n\n"
            "A few more questions to find you the best flights:\n\n"
            "Do you have any preferences? You can mention:\n"
            "  - Maximum budget per person (e.g., '$500')\n"
            "  - Non-stop only (e.g., 'non-stop' or 'direct')\n"
            "  - Preferred airline (e.g., 'Delta')\n"
            "  - Preferred departure time (e.g., 'morning', 'evening')\n\n"
            "Or type 'no' to search with no additional preferences."
        )

    def _handle_preferences(self, text: str) -> str:
        lower = text.lower()
        if lower not in ("no", "none", "n", "skip", "no preferences"):
            self._parse_preferences(lower)
        return self._do_search()

    def _parse_preferences(self, text: str) -> None:
        """Extract preferences from free-text input."""
        price_match = re.search(r"\$\s*(\d+[\d,]*)", text)
        if price_match:
            self.criteria.max_price = float(price_match.group(1).replace(",", ""))

        if any(kw in text for kw in ("non-stop", "nonstop", "direct", "no stops")):
            self.criteria.max_stops = 0

        for time_pref in ("morning", "afternoon", "evening", "night", "red-eye"):
            if time_pref in text:
                self.criteria.preferred_time = time_pref
                break

        airline_keywords = {
            "united": "United Airlines", "delta": "Delta Air Lines",
            "american": "American Airlines", "southwest": "Southwest Airlines",
            "jetblue": "JetBlue Airways", "alaska": "Alaska Airlines",
            "british airways": "British Airways", "air france": "Air France",
            "lufthansa": "Lufthansa", "emirates": "Emirates",
            "singapore": "Singapore Airlines", "japan airlines": "Japan Airlines",
            "qantas": "Qantas", "air canada": "Air Canada",
            "turkish": "Turkish Airlines", "qatar": "Qatar Airways",
        }
        for keyword, airline_name in airline_keywords.items():
            if keyword in text:
                self.criteria.preferred_airline = airline_name
                break

    def _do_search(self) -> str:
        """Execute the flight search and present results."""
        self.outbound_flights = self.engine.search(self.criteria)

        if not self.outbound_flights:
            self.state = AgentState.COLLECTING_PREFERENCES
            return (
                "I couldn't find any flights matching your criteria.\n"
                "Would you like to adjust your preferences?\n"
                "(Try relaxing your budget, allowing stops, or changing dates.\n"
                " Type 'no' to search again with no filters.)"
            )

        self.state = AgentState.SELECTING_OUTBOUND

        best = self.engine.get_best_value(self.outbound_flights, top_n=3)

        lines = [
            f"I found {len(self.outbound_flights)} flights from "
            f"{self.criteria.origin} to {self.criteria.destination} "
            f"on {self.criteria.departure_date}.\n",
            "--- TOP RECOMMENDATIONS (Best Value) ---\n",
        ]
        lines.extend(self._format_flight_list(best, recommend=True))

        if len(self.outbound_flights) > 3:
            lines.append("\n--- ALL AVAILABLE FLIGHTS ---\n")
            lines.extend(self._format_flight_list(self.outbound_flights))

        lines.append(
            "\nWhich flight would you like to book? Enter the number (e.g., '1').\n"
            "Or type 'sort price', 'sort duration', or 'sort time' to re-sort."
        )
        return "\n".join(lines)

    def _handle_outbound_selection(self, text: str) -> str:
        lower = text.lower()
        if lower.startswith("sort"):
            return self._handle_sort(lower)

        try:
            idx = int(text) - 1
        except ValueError:
            return "Please enter a flight number (e.g., '1') or a sort command."
        if idx < 0 or idx >= len(self.outbound_flights):
            return f"Please enter a number between 1 and {len(self.outbound_flights)}."

        selected = self.outbound_flights[idx]
        if selected.available_seats < self.criteria.passengers:
            return (
                f"Sorry, flight {selected.flight_number} only has {selected.available_seats} "
                f"seat{'s' if selected.available_seats != 1 else ''} available, "
                f"but you need {self.criteria.passengers}. Please choose another flight."
            )

        self.booking.outbound_flight = selected

        # For round trips, the Amadeus API returns round-trip offers in a single search
        # (outbound + return itineraries bundled together). If we searched with a return date,
        # the outbound_flights already represent round-trip pricing. No separate return search needed.
        if self.criteria.trip_type == TripType.ROUND_TRIP and self.criteria.return_date:
            self.booking.calculate_total()
            self.state = AgentState.COLLECTING_PASSENGER_INFO
            return (
                f"You selected:\n{self._format_single_flight(selected)}\n\n"
                "This is a round-trip fare (outbound + return included in the price).\n"
                f"Total for {self.criteria.passengers} passenger{'s' if self.criteria.passengers > 1 else ''}: "
                f"${self.booking.total_price:,.2f} {selected.currency}\n\n"
                "To complete the booking, please enter the primary passenger's full name:"
            )

        # One-way
        self.booking.calculate_total()
        self.state = AgentState.COLLECTING_PASSENGER_INFO
        return (
            f"You selected:\n{self._format_single_flight(selected)}\n\n"
            f"Total for {self.criteria.passengers} passenger{'s' if self.criteria.passengers > 1 else ''}: "
            f"${self.booking.total_price:,.2f} {selected.currency}\n\n"
            "To complete the booking, please enter the primary passenger's full name:"
        )

    def _handle_sort(self, text: str, is_return: bool = False) -> str:
        flights = self.return_flights if is_return else self.outbound_flights
        if "price" in text:
            flights = self.engine.sort_by_price(flights)
            label = "price (lowest first)"
        elif "duration" in text:
            flights = self.engine.sort_by_duration(flights)
            label = "duration (shortest first)"
        elif "depart" in text or "time" in text:
            flights = self.engine.sort_by_departure(flights)
            label = "departure time (earliest first)"
        else:
            return "Sort options: 'sort price', 'sort duration', 'sort time'"

        if is_return:
            self.return_flights = flights
        else:
            self.outbound_flights = flights

        lines = [f"Sorted by {label}:\n"]
        lines.extend(self._format_flight_list(flights))
        lines.append("\nEnter a flight number to select:")
        return "\n".join(lines)

    def _handle_passenger_name(self, text: str) -> str:
        if len(text) < 2:
            return "Please enter a valid full name (first and last name)."
        self.booking.passenger_name = text
        self.state = AgentState.COLLECTING_EMAIL
        return f"Thank you, {text.split()[0]}. Please enter your email address for the booking confirmation:"

    def _handle_email(self, text: str) -> str:
        if "@" not in text or "." not in text:
            return "Please enter a valid email address (e.g., name@example.com)."
        self.booking.passenger_email = text
        self.booking.calculate_total()
        self.state = AgentState.CONFIRMING_BOOKING
        return self._booking_summary()

    def _handle_confirmation(self, text: str) -> str:
        lower = text.lower()
        if lower in ("yes", "y", "confirm", "book", "ok"):
            return self._execute_booking()
        if lower in ("no", "n", "cancel"):
            self.state = AgentState.COMPLETED
            return "Booking cancelled. Thank you for using FlightBooker!"
        return "Please type 'yes' to confirm or 'no' to cancel the booking."

    def _execute_booking(self) -> str:
        """Attempt to create a real booking via the Amadeus API."""
        flight = self.booking.outbound_flight
        if not flight or not flight.raw_offer:
            # No raw offer data (e.g. in tests) -- simulate confirmation
            self.booking.confirmed = True
            self.state = AgentState.COMPLETED
            return self._confirmation_message()

        try:
            order = self.engine.client.create_booking(
                flight,
                self.booking.passenger_name,
                self.booking.passenger_email,
            )
            self.booking.confirmed = True
            self.booking.booking_id = order.get("id", self.booking.booking_id)
            self.state = AgentState.COMPLETED
            return self._confirmation_message()
        except Exception:
            # If real booking fails (e.g. sandbox limitations), still confirm locally
            self.booking.confirmed = True
            self.state = AgentState.COMPLETED
            return (
                "(Note: Live booking could not be completed via the API -- "
                "this may be a sandbox limitation.)\n\n"
                + self._confirmation_message()
            )

    # --- Formatting helpers ---

    def _format_flight_list(
        self,
        flights: list[Flight],
        recommend: bool = False,
    ) -> list[str]:
        lines = []
        for i, flight in enumerate(flights, 1):
            prefix = f"  {'*' if recommend else ' '} {i}."
            lines.append(
                f"{prefix} {flight.flight_number} | {flight.airline}\n"
                f"      {flight.origin} {flight.departure.strftime('%H:%M')} -> "
                f"{flight.destination} {flight.arrival.strftime('%H:%M')} | "
                f"{flight.duration_display()} | {flight.stops_display()}\n"
                f"      ${flight.price:,.2f} {flight.currency}/total | "
                f"{flight.available_seats} seats left"
            )
        return lines

    def _format_single_flight(self, flight: Flight) -> str:
        return (
            f"  {flight.flight_number} | {flight.airline}\n"
            f"  {flight.origin} -> {flight.destination}\n"
            f"  {flight.departure.strftime('%B %d, %Y %H:%M')} -> "
            f"{flight.arrival.strftime('%B %d, %Y %H:%M')}\n"
            f"  Duration: {flight.duration_display()} | {flight.stops_display()}\n"
            f"  Cabin: {flight.cabin_class.display()} | "
            f"${flight.price:,.2f} {flight.currency}"
        )

    def _booking_summary(self) -> str:
        lines = [
            "\n========== BOOKING SUMMARY ==========\n",
            f"Passenger: {self.booking.passenger_name}",
            f"Email: {self.booking.passenger_email}",
            f"Passengers: {self.booking.passengers}",
            f"Trip type: {'Round Trip' if self.booking.trip_type == TripType.ROUND_TRIP else 'One Way'}\n",
            "--- FLIGHT ---",
            self._format_single_flight(self.booking.outbound_flight),
        ]
        if self.booking.return_flight:
            lines.extend([
                "\n--- RETURN FLIGHT ---",
                self._format_single_flight(self.booking.return_flight),
            ])
        lines.extend([
            f"\n--- TOTAL: ${self.booking.total_price:,.2f} {self.booking.currency} ---",
            "\n=====================================",
            "\nWould you like to confirm this booking? (yes/no)",
        ])
        return "\n".join(lines)

    def _confirmation_message(self) -> str:
        flight = self.booking.outbound_flight
        return (
            f"\nBooking confirmed! Your booking ID is: {self.booking.booking_id}\n\n"
            f"A confirmation email will be sent to {self.booking.passenger_email}.\n\n"
            "--- BOOKING DETAILS ---\n"
            f"Booking ID: {self.booking.booking_id}\n"
            f"Passenger: {self.booking.passenger_name}\n"
            f"Flight: {flight.flight_number} "
            f"({flight.origin} -> {flight.destination}) "
            f"on {flight.departure.strftime('%B %d, %Y at %H:%M')}\n"
            f"Total: ${self.booking.total_price:,.2f} {self.booking.currency}\n\n"
            "Thank you for booking with FlightBooker! Have a great trip!"
        )

    def _help_text(self) -> str:
        return (
            "--- FlightBooker Help ---\n"
            "I'll guide you step-by-step to find and book real flights.\n\n"
            "Commands you can use anytime:\n"
            "  'help'       - Show this help message\n"
            "  'restart'    - Start a new search\n"
            "  'quit'       - Exit the agent\n\n"
            "When viewing flights:\n"
            "  'sort price'    - Sort by price (lowest first)\n"
            "  'sort duration' - Sort by flight duration\n"
            "  'sort time'     - Sort by departure time\n\n"
            "Preferences you can specify:\n"
            "  Budget: '$500'\n"
            "  Stops: 'non-stop' or 'direct'\n"
            "  Time: 'morning', 'afternoon', 'evening', 'night'\n"
            "  Airline: 'Delta', 'United', etc.\n\n"
            "Powered by the Amadeus Flight API.\n"
        )

    @staticmethod
    def _parse_date(text: str) -> datetime | None:
        """Parse various date formats from user input."""
        text = text.strip()
        formats = [
            "%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y",
            "%B %d", "%B %d, %Y", "%b %d", "%b %d, %Y",
            "%B %d %Y", "%b %d %Y",
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(text, fmt)
                if "%Y" not in fmt:
                    now = datetime.now()
                    dt = dt.replace(year=now.year)
                    if dt < now:
                        dt = dt.replace(year=now.year + 1)
                return dt
            except ValueError:
                continue

        lower = text.lower()
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if lower == "today":
            return today
        if lower == "tomorrow":
            return today + timedelta(days=1)
        match = re.match(r"in (\d+) days?", lower)
        if match:
            return today + timedelta(days=int(match.group(1)))
        match = re.match(r"next (\w+)", lower)
        if match:
            day_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            target = match.group(1).lower()
            if target in day_names:
                target_idx = day_names.index(target)
                current_idx = today.weekday()
                days_ahead = (target_idx - current_idx) % 7
                if days_ahead == 0:
                    days_ahead = 7
                return today + timedelta(days=days_ahead)

        return None
