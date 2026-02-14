"""Tests for the flight search engine (with mocked Amadeus client)."""

from __future__ import annotations

from datetime import datetime, timedelta

from flight_booking.models import CabinClass, Flight, SearchCriteria
from flight_booking.search import FlightSearchEngine

from .conftest import make_flight


class TestFlightSearchEngine:
    def test_search_returns_flights(self, mock_client):
        engine = FlightSearchEngine(mock_client)
        criteria = SearchCriteria(origin="JFK", destination="LAX", departure_date="2026-06-15")

        results = engine.search(criteria)

        assert len(results) == 3
        mock_client.search_flights.assert_called_once()

    def test_search_handles_api_error(self, mock_client):
        from flight_booking.amadeus_client import FlightSearchError
        mock_client.search_flights.side_effect = FlightSearchError("API error")
        engine = FlightSearchEngine(mock_client)
        criteria = SearchCriteria(origin="JFK", destination="LAX", departure_date="2026-06-15")

        results = engine.search(criteria)

        assert results == []

    def test_resolve_location(self, mock_client):
        engine = FlightSearchEngine(mock_client)

        results = engine.resolve_location("New York")

        assert len(results) == 1
        assert results[0]["iata"] == "JFK"

    def test_resolve_location_multi(self, mock_client):
        engine = FlightSearchEngine(mock_client)

        results = engine.resolve_location("London")

        assert len(results) == 3
        codes = [r["iata"] for r in results]
        assert "LHR" in codes
        assert "LGW" in codes

    def test_filter_preferred_airline(self, mock_client):
        engine = FlightSearchEngine(mock_client)
        criteria = SearchCriteria(
            origin="JFK", destination="LAX", departure_date="2026-06-15",
            preferred_airline="Delta",
        )

        results = engine.search(criteria)

        # Delta should come first
        assert "DELTA" in results[0].airline.upper()

    def test_filter_preferred_time(self, mock_client):
        engine = FlightSearchEngine(mock_client)
        criteria = SearchCriteria(
            origin="JFK", destination="LAX", departure_date="2026-06-15",
            preferred_time="evening",
        )

        results = engine.search(criteria)

        # The evening flight (18:30) should be first
        assert results[0].departure.hour >= 17


class TestSorting:
    def test_sort_by_price(self):
        flights = [make_flight(price=300), make_flight(price=200), make_flight(price=400)]
        sorted_flights = FlightSearchEngine.sort_by_price(flights)
        prices = [f.price for f in sorted_flights]
        assert prices == [200, 300, 400]

    def test_sort_by_duration(self):
        flights = [
            make_flight(duration_hours=6),
            make_flight(duration_hours=4),
            make_flight(duration_hours=5),
        ]
        sorted_flights = FlightSearchEngine.sort_by_duration(flights)
        durations = [f.duration_hours for f in sorted_flights]
        assert durations == [4.0, 5.0, 6.0]

    def test_sort_by_departure(self):
        flights = [
            make_flight(hour=14),
            make_flight(hour=8),
            make_flight(hour=20),
        ]
        sorted_flights = FlightSearchEngine.sort_by_departure(flights)
        hours = [f.departure.hour for f in sorted_flights]
        assert hours == [8, 14, 20]


class TestBestValue:
    def test_get_best_value_returns_top_n(self):
        flights = [
            make_flight(price=200, duration_hours=8),
            make_flight(price=300, duration_hours=5),
            make_flight(price=250, duration_hours=6),
            make_flight(price=500, duration_hours=4),
        ]
        best = FlightSearchEngine.get_best_value(flights, top_n=2)
        assert len(best) == 2

    def test_get_best_value_empty(self):
        best = FlightSearchEngine.get_best_value([], top_n=3)
        assert best == []

    def test_best_value_favors_price(self):
        flights = [
            make_flight(price=200, duration_hours=7),
            make_flight(price=500, duration_hours=4),
        ]
        best = FlightSearchEngine.get_best_value(flights, top_n=1)
        assert best[0].price == 200
