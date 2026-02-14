"""Tests for the Amadeus API client (parsing logic, mocked HTTP)."""

from __future__ import annotations

from flight_booking.amadeus_client import AmadeusFlightClient

from .conftest import SAMPLE_AMADEUS_RESPONSE


class TestFlightOfferParsing:
    """Test _parse_flight_offers without hitting the real API."""

    def _make_client(self) -> AmadeusFlightClient:
        return object.__new__(AmadeusFlightClient)

    def test_parse_direct_flight(self):
        client = self._make_client()
        carriers = SAMPLE_AMADEUS_RESPONSE["dictionaries"]["carriers"]
        offers = [SAMPLE_AMADEUS_RESPONSE["data"][0]]

        flights = client._parse_flight_offers(offers, carriers, "ECONOMY")

        assert len(flights) == 1
        f = flights[0]
        assert f.flight_number == "UA100"
        assert f.airline == "UNITED AIRLINES"
        assert f.origin == "JFK"
        assert f.destination == "LAX"
        assert f.price == 289.99
        assert f.currency == "USD"
        assert f.stops == 0
        assert f.cabin_class == "ECONOMY"
        assert f.available_seats == 9

    def test_parse_connecting_flight(self):
        client = self._make_client()
        carriers = SAMPLE_AMADEUS_RESPONSE["dictionaries"]["carriers"]
        offers = [SAMPLE_AMADEUS_RESPONSE["data"][1]]

        flights = client._parse_flight_offers(offers, carriers, "ECONOMY")

        assert len(flights) == 1
        f = flights[0]
        assert f.flight_number == "DL200"
        assert f.stops == 1
        assert f.layover_airports == ["ORD"]
        assert f.origin == "JFK"
        assert f.destination == "LAX"

    def test_parse_multiple_offers(self):
        client = self._make_client()
        carriers = SAMPLE_AMADEUS_RESPONSE["dictionaries"]["carriers"]

        flights = client._parse_flight_offers(
            SAMPLE_AMADEUS_RESPONSE["data"], carriers, "ECONOMY"
        )

        assert len(flights) == 2
        prices = [f.price for f in flights]
        assert 289.99 in prices
        assert 219.50 in prices

    def test_parse_empty(self):
        client = self._make_client()
        flights = client._parse_flight_offers([], {}, "ECONOMY")
        assert flights == []

    def test_parse_preserves_raw_offer(self):
        client = self._make_client()
        carriers = SAMPLE_AMADEUS_RESPONSE["dictionaries"]["carriers"]
        offer = SAMPLE_AMADEUS_RESPONSE["data"][0]

        flights = client._parse_flight_offers([offer], carriers, "ECONOMY")
        assert flights[0].raw_offer == offer

    def test_duration_display(self):
        client = self._make_client()
        carriers = SAMPLE_AMADEUS_RESPONSE["dictionaries"]["carriers"]
        offers = [SAMPLE_AMADEUS_RESPONSE["data"][0]]

        flights = client._parse_flight_offers(offers, carriers, "ECONOMY")
        assert flights[0].duration_display() == "3h 30m"


class TestHotelOfferParsing:
    def _make_client(self) -> AmadeusFlightClient:
        return object.__new__(AmadeusFlightClient)

    def test_parse_available_hotel(self):
        client = self._make_client()
        data = [{
            "available": True,
            "hotel": {
                "hotelId": "H123",
                "name": "Grand Hotel",
                "chainCode": "GH",
                "cityCode": "PAR",
            },
            "offers": [{
                "id": "OFF1",
                "checkInDate": "2026-04-01",
                "checkOutDate": "2026-04-05",
                "room": {
                    "typeEstimated": {"category": "DELUXE", "beds": 2, "bedType": "KING"},
                    "description": {"text": "Nice room"},
                },
                "price": {"total": "500.00", "currency": "EUR"},
                "boardType": "BREAKFAST",
                "policies": {"cancellation": {"deadline": "2026-03-28"}},
            }],
        }]
        offers = client._parse_hotel_offers(data)
        assert len(offers) == 1
        o = offers[0]
        assert o.hotel.name == "Grand Hotel"
        assert o.price == 500.0
        assert o.room_type == "DELUXE"
        assert "2026-03-28" in o.cancellation_info

    def test_parse_unavailable_hotel(self):
        client = self._make_client()
        data = [{"available": False, "hotel": {}, "offers": []}]
        assert client._parse_hotel_offers(data) == []
