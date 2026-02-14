"""Tests for the Amadeus API client (with mocked HTTP calls)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from flight_booking.amadeus_client import AmadeusFlightClient, FlightSearchError
from flight_booking.models import CabinClass, SearchCriteria

from .conftest import SAMPLE_AMADEUS_RESPONSE, SAMPLE_LOCATION_RESPONSE_SINGLE


class TestAmadeusClientParsing:
    """Test the response parsing logic without hitting the real API."""

    def test_parse_offers_direct_flight(self):
        client = object.__new__(AmadeusFlightClient)
        criteria = SearchCriteria(origin="JFK", destination="LAX", departure_date="2026-06-15")
        carriers = SAMPLE_AMADEUS_RESPONSE["dictionaries"]["carriers"]
        offers = [SAMPLE_AMADEUS_RESPONSE["data"][0]]

        flights = client._parse_offers(offers, carriers, criteria)

        assert len(flights) == 1
        f = flights[0]
        assert f.flight_number == "UA100"
        assert f.airline == "UNITED AIRLINES"
        assert f.origin == "JFK"
        assert f.destination == "LAX"
        assert f.price == 289.99
        assert f.currency == "USD"
        assert f.stops == 0
        assert f.cabin_class == CabinClass.ECONOMY
        assert f.available_seats == 9

    def test_parse_offers_connecting_flight(self):
        client = object.__new__(AmadeusFlightClient)
        criteria = SearchCriteria(origin="JFK", destination="LAX", departure_date="2026-06-15")
        carriers = SAMPLE_AMADEUS_RESPONSE["dictionaries"]["carriers"]
        offers = [SAMPLE_AMADEUS_RESPONSE["data"][1]]

        flights = client._parse_offers(offers, carriers, criteria)

        assert len(flights) == 1
        f = flights[0]
        assert f.flight_number == "DL200"
        assert f.stops == 1
        assert f.layover_airports == ["ORD"]
        assert f.origin == "JFK"
        assert f.destination == "LAX"

    def test_parse_offers_multiple(self):
        client = object.__new__(AmadeusFlightClient)
        criteria = SearchCriteria(origin="JFK", destination="LAX", departure_date="2026-06-15")
        carriers = SAMPLE_AMADEUS_RESPONSE["dictionaries"]["carriers"]

        flights = client._parse_offers(SAMPLE_AMADEUS_RESPONSE["data"], carriers, criteria)

        assert len(flights) == 3
        prices = [f.price for f in flights]
        assert 289.99 in prices
        assert 219.50 in prices
        assert 349.00 in prices

    def test_parse_offers_empty(self):
        client = object.__new__(AmadeusFlightClient)
        criteria = SearchCriteria(origin="JFK", destination="LAX", departure_date="2026-06-15")

        flights = client._parse_offers([], {}, criteria)

        assert flights == []

    def test_parse_offers_preserves_raw_offer(self):
        client = object.__new__(AmadeusFlightClient)
        criteria = SearchCriteria(origin="JFK", destination="LAX", departure_date="2026-06-15")
        carriers = SAMPLE_AMADEUS_RESPONSE["dictionaries"]["carriers"]
        offer = SAMPLE_AMADEUS_RESPONSE["data"][0]

        flights = client._parse_offers([offer], carriers, criteria)

        assert flights[0].raw_offer == offer
