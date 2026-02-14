"""Shared test fixtures with mock Amadeus API responses."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from flight_booking.amadeus_client import AmadeusFlightClient
from flight_booking.models import CabinClass, Flight


def make_flight(
    flight_number: str = "UA100",
    airline: str = "United Airlines",
    airline_code: str = "UA",
    origin: str = "JFK",
    destination: str = "LAX",
    hour: int = 10,
    duration_hours: float = 5.5,
    price: float = 300.0,
    currency: str = "USD",
    cabin_class: CabinClass = CabinClass.ECONOMY,
    stops: int = 0,
    available_seats: int = 9,
    layover_airports: list[str] | None = None,
) -> Flight:
    departure = datetime(2026, 6, 15, hour, 0)
    arrival = departure + timedelta(hours=duration_hours)
    return Flight(
        flight_number=flight_number,
        airline=airline,
        airline_code=airline_code,
        origin=origin,
        destination=destination,
        departure=departure,
        arrival=arrival,
        price=price,
        currency=currency,
        cabin_class=cabin_class,
        stops=stops,
        available_seats=available_seats,
        layover_airports=layover_airports or [],
    )


# A realistic Amadeus API response for JFK -> LAX
SAMPLE_AMADEUS_RESPONSE = {
    "data": [
        {
            "type": "flight-offer",
            "id": "1",
            "numberOfBookableSeats": 9,
            "itineraries": [
                {
                    "segments": [
                        {
                            "departure": {"iataCode": "JFK", "at": "2026-06-15T08:00:00"},
                            "arrival": {"iataCode": "LAX", "at": "2026-06-15T11:30:00"},
                            "carrierCode": "UA",
                            "number": "100",
                        }
                    ]
                }
            ],
            "price": {"grandTotal": "289.99", "currency": "USD"},
            "travelerPricings": [
                {
                    "fareDetailsBySegment": [{"cabin": "ECONOMY"}]
                }
            ],
        },
        {
            "type": "flight-offer",
            "id": "2",
            "numberOfBookableSeats": 4,
            "itineraries": [
                {
                    "segments": [
                        {
                            "departure": {"iataCode": "JFK", "at": "2026-06-15T14:00:00"},
                            "arrival": {"iataCode": "ORD", "at": "2026-06-15T16:30:00"},
                            "carrierCode": "DL",
                            "number": "200",
                        },
                        {
                            "departure": {"iataCode": "ORD", "at": "2026-06-15T18:00:00"},
                            "arrival": {"iataCode": "LAX", "at": "2026-06-15T20:00:00"},
                            "carrierCode": "DL",
                            "number": "201",
                        },
                    ]
                }
            ],
            "price": {"grandTotal": "219.50", "currency": "USD"},
            "travelerPricings": [
                {
                    "fareDetailsBySegment": [{"cabin": "ECONOMY"}, {"cabin": "ECONOMY"}]
                }
            ],
        },
        {
            "type": "flight-offer",
            "id": "3",
            "numberOfBookableSeats": 7,
            "itineraries": [
                {
                    "segments": [
                        {
                            "departure": {"iataCode": "JFK", "at": "2026-06-15T18:30:00"},
                            "arrival": {"iataCode": "LAX", "at": "2026-06-15T22:00:00"},
                            "carrierCode": "B6",
                            "number": "300",
                        }
                    ]
                }
            ],
            "price": {"grandTotal": "349.00", "currency": "USD"},
            "travelerPricings": [
                {
                    "fareDetailsBySegment": [{"cabin": "ECONOMY"}]
                }
            ],
        },
    ],
    "dictionaries": {
        "carriers": {
            "UA": "UNITED AIRLINES",
            "DL": "DELTA AIR LINES",
            "B6": "JETBLUE AIRWAYS",
        }
    },
}

SAMPLE_LOCATION_RESPONSE_SINGLE = {
    "data": [
        {
            "iataCode": "JFK",
            "name": "JOHN F KENNEDY INTL",
            "subType": "AIRPORT",
            "address": {"cityName": "NEW YORK", "countryCode": "US"},
        }
    ]
}

SAMPLE_LOCATION_RESPONSE_MULTI = {
    "data": [
        {
            "iataCode": "LHR",
            "name": "HEATHROW",
            "subType": "AIRPORT",
            "address": {"cityName": "LONDON", "countryCode": "GB"},
        },
        {
            "iataCode": "LGW",
            "name": "GATWICK",
            "subType": "AIRPORT",
            "address": {"cityName": "LONDON", "countryCode": "GB"},
        },
        {
            "iataCode": "STN",
            "name": "STANSTED",
            "subType": "AIRPORT",
            "address": {"cityName": "LONDON", "countryCode": "GB"},
        },
    ]
}


@pytest.fixture
def mock_client():
    """Return a mock AmadeusFlightClient whose API calls return sample data."""
    client = MagicMock(spec=AmadeusFlightClient)

    # Mock search_flights to return parsed Flight objects from sample data
    def _search_flights(criteria):
        from flight_booking.amadeus_client import AmadeusFlightClient as RealClient
        real = object.__new__(RealClient)
        carriers = SAMPLE_AMADEUS_RESPONSE["dictionaries"]["carriers"]
        return real._parse_offers(SAMPLE_AMADEUS_RESPONSE["data"], carriers, criteria)

    client.search_flights.side_effect = _search_flights

    # Mock search_locations
    def _search_locations(keyword):
        kw = keyword.lower()
        if "london" in kw:
            data = SAMPLE_LOCATION_RESPONSE_MULTI["data"]
        else:
            data = SAMPLE_LOCATION_RESPONSE_SINGLE["data"]
        results = []
        for loc in data:
            results.append({
                "iata": loc.get("iataCode", ""),
                "name": loc.get("name", ""),
                "city": loc.get("address", {}).get("cityName", ""),
                "country": loc.get("address", {}).get("countryCode", ""),
                "type": loc.get("subType", ""),
            })
        return results

    client.search_locations.side_effect = _search_locations

    # Mock create_booking
    client.create_booking.return_value = {"id": "MOCK12345"}

    return client
