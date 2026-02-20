"""In-memory flight data store for demonstration purposes."""

from datetime import datetime
from app.models import Flight

# Sample flight data — in production this would come from a database or external API.
SAMPLE_FLIGHTS: list[Flight] = [
    Flight(
        flight_id="FL001",
        airline="SkyWay Airlines",
        origin="JFK",
        destination="LAX",
        departure=datetime(2026, 3, 15, 8, 0),
        arrival=datetime(2026, 3, 15, 11, 30),
        price=349.99,
        seats_available=42,
    ),
    Flight(
        flight_id="FL002",
        airline="SkyWay Airlines",
        origin="JFK",
        destination="LAX",
        departure=datetime(2026, 3, 15, 14, 0),
        arrival=datetime(2026, 3, 15, 17, 30),
        price=289.99,
        seats_available=15,
    ),
    Flight(
        flight_id="FL003",
        airline="Pacific Air",
        origin="LAX",
        destination="JFK",
        departure=datetime(2026, 3, 16, 9, 0),
        arrival=datetime(2026, 3, 16, 17, 0),
        price=319.99,
        seats_available=30,
    ),
    Flight(
        flight_id="FL004",
        airline="Atlantic Express",
        origin="JFK",
        destination="LHR",
        departure=datetime(2026, 3, 17, 20, 0),
        arrival=datetime(2026, 3, 18, 8, 0),
        price=599.99,
        seats_available=8,
    ),
    Flight(
        flight_id="FL005",
        airline="Pacific Air",
        origin="SFO",
        destination="NRT",
        departure=datetime(2026, 3, 18, 12, 0),
        arrival=datetime(2026, 3, 19, 16, 0),
        price=849.99,
        seats_available=22,
    ),
]


def search_flights(origin: str, destination: str, departure_date: str) -> list[Flight]:
    """Search flights by origin, destination, and departure date (YYYY-MM-DD)."""
    results = []
    for flight in SAMPLE_FLIGHTS:
        if (
            flight.origin.upper() == origin.upper()
            and flight.destination.upper() == destination.upper()
            and flight.departure.strftime("%Y-%m-%d") == departure_date
            and flight.seats_available > 0
        ):
            results.append(flight)
    return results


def get_flight(flight_id: str) -> Flight | None:
    """Retrieve a single flight by ID."""
    for flight in SAMPLE_FLIGHTS:
        if flight.flight_id == flight_id:
            return flight
    return None
