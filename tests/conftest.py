"""Shared test fixtures for the Voyager travel agent."""

from __future__ import annotations

import os
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from flight_booking.amadeus_client import (
    AmadeusFlightClient,
    RawActivity,
    RawFlight,
    RawHotel,
    RawHotelOffer,
    RawPointOfInterest,
)
from flight_booking.tools import ToolExecutor


# Realistic Amadeus API response for parsing tests
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
        },
    ],
    "dictionaries": {
        "carriers": {"UA": "UNITED AIRLINES", "DL": "DELTA AIR LINES"}
    },
}


@pytest.fixture
def mock_amadeus():
    """Return a mocked AmadeusFlightClient."""
    client = MagicMock(spec=AmadeusFlightClient)
    client.search_flights.return_value = []
    client.search_hotels_by_city.return_value = []
    client.search_hotel_offers.return_value = []
    client.search_activities.return_value = []
    client.search_pois.return_value = []
    client.search_locations.return_value = []
    client.get_city_coordinates.return_value = None
    client.create_flight_booking.return_value = {"id": "API-123"}
    return client


@pytest.fixture
def executor(mock_amadeus, tmp_path):
    """Return a ToolExecutor with a mocked client and temp output dir."""
    ex = ToolExecutor(client=mock_amadeus)
    ex.output_dir = str(tmp_path / "trip_documents")
    os.makedirs(ex.output_dir, exist_ok=True)
    return ex


@pytest.fixture
def sample_raw_flights():
    """Return sample RawFlight objects."""
    return [
        RawFlight(
            flight_number="AA100",
            airline="American Airlines",
            airline_code="AA",
            origin="JFK",
            destination="LAX",
            departure=datetime(2026, 3, 15, 8, 0),
            arrival=datetime(2026, 3, 15, 11, 30),
            price=350.00,
            currency="USD",
            cabin_class="ECONOMY",
            stops=0,
            available_seats=5,
            raw_offer={"price": {"grandTotal": "350.00"}},
        ),
        RawFlight(
            flight_number="DL200",
            airline="Delta Air Lines",
            airline_code="DL",
            origin="JFK",
            destination="LAX",
            departure=datetime(2026, 3, 15, 14, 0),
            arrival=datetime(2026, 3, 15, 17, 45),
            price=425.00,
            currency="USD",
            cabin_class="ECONOMY",
            stops=1,
            available_seats=3,
            layover_airports=["ORD"],
            raw_offer={"price": {"grandTotal": "425.00"}},
        ),
    ]


@pytest.fixture
def sample_raw_hotels():
    """Return sample RawHotelOffer objects."""
    hotel = RawHotel(
        hotel_id="HTPAR001",
        name="Hotel Le Marais",
        chain_code="XX",
        city_code="PAR",
        latitude=48.8566,
        longitude=2.3522,
        address="FR",
    )
    return [hotel], [
        RawHotelOffer(
            offer_id="OFF-001",
            hotel=hotel,
            check_in="2026-04-10",
            check_out="2026-04-14",
            room_type="DOUBLE",
            room_description="Deluxe Room with City View",
            beds=1,
            bed_type="DOUBLE",
            board_type="BREAKFAST",
            price=800.00,
            currency="USD",
            cancellation_info="Free cancellation before 2026-04-08",
            raw_offer={"id": "OFF-001"},
        ),
    ]


@pytest.fixture
def sample_raw_activities():
    return [
        RawActivity(
            activity_id="ACT-001",
            name="Eiffel Tower Skip-the-Line",
            description="Skip the long lines!",
            price=45.00,
            currency="USD",
            rating="4.7",
            booking_link="https://example.com/eiffel",
        ),
    ]


@pytest.fixture
def sample_raw_pois():
    return [
        RawPointOfInterest(
            poi_id="POI-001",
            name="Louvre Museum",
            category="SIGHTS",
            latitude=48.8606,
            longitude=2.3376,
            tags=["museum", "art", "landmark"],
        ),
    ]


@pytest.fixture
def sample_locations():
    return [
        {"iata": "JFK", "name": "JOHN F KENNEDY INTL", "city": "NEW YORK", "country": "US", "type": "AIRPORT"},
        {"iata": "NYC", "name": "NEW YORK", "city": "NEW YORK", "country": "US", "type": "CITY"},
    ]
