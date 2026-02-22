"""Mock flight data and search logic."""

from app.models import CabinClass, Flight

FLIGHTS: list[Flight] = [
    Flight(
        flight_id="FA101",
        airline="FlyAhead",
        origin="JFK",
        destination="LAX",
        departure="2026-03-15T08:00:00",
        arrival="2026-03-15T11:30:00",
        price=320.00,
        cabin_class=CabinClass.economy,
        seats_available=42,
    ),
    Flight(
        flight_id="FA102",
        airline="FlyAhead",
        origin="JFK",
        destination="LAX",
        departure="2026-03-15T14:00:00",
        arrival="2026-03-15T17:30:00",
        price=850.00,
        cabin_class=CabinClass.business,
        seats_available=8,
    ),
    Flight(
        flight_id="SK200",
        airline="SkyBridge",
        origin="SFO",
        destination="ORD",
        departure="2026-03-16T06:00:00",
        arrival="2026-03-16T12:15:00",
        price=275.00,
        cabin_class=CabinClass.economy,
        seats_available=55,
    ),
    Flight(
        flight_id="SK201",
        airline="SkyBridge",
        origin="ORD",
        destination="MIA",
        departure="2026-03-16T09:00:00",
        arrival="2026-03-16T13:20:00",
        price=210.00,
        cabin_class=CabinClass.economy,
        seats_available=30,
    ),
    Flight(
        flight_id="FA300",
        airline="FlyAhead",
        origin="LAX",
        destination="JFK",
        departure="2026-03-17T07:00:00",
        arrival="2026-03-17T15:15:00",
        price=1450.00,
        cabin_class=CabinClass.first,
        seats_available=4,
    ),
]


def search_flights(
    origin: str | None = None,
    destination: str | None = None,
    date: str | None = None,
    cabin_class: CabinClass | None = None,
) -> list[Flight]:
    results = FLIGHTS
    if origin:
        results = [f for f in results if f.origin.upper() == origin.upper()]
    if destination:
        results = [f for f in results if f.destination.upper() == destination.upper()]
    if date:
        results = [f for f in results if f.departure.startswith(date)]
    if cabin_class:
        results = [f for f in results if f.cabin_class == cabin_class]
    return results
