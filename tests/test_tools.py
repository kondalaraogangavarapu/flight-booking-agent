"""Tests for the tool executor — core business logic."""

from __future__ import annotations

import json
import os

from flight_booking.tools import TOOL_DEFINITIONS, ToolExecutor, _markup


class TestMarkup:
    def test_markup_10_percent(self):
        assert _markup(100.0) == 110.0

    def test_markup_rounds(self):
        assert _markup(99.99) == 109.99

    def test_markup_zero(self):
        assert _markup(0) == 0.0


class TestToolDefinitions:
    def test_eight_tools_defined(self):
        assert len(TOOL_DEFINITIONS) == 8

    def test_all_have_required_fields(self):
        for tool in TOOL_DEFINITIONS:
            assert "name" in tool
            assert "description" in tool
            assert "input_schema" in tool
            assert tool["input_schema"]["type"] == "object"

    def test_tool_names(self):
        names = {t["name"] for t in TOOL_DEFINITIONS}
        expected = {
            "search_flights", "search_hotels", "search_activities",
            "search_points_of_interest", "resolve_location",
            "book_flight", "book_hotel", "create_trip_presentation",
        }
        assert names == expected


class TestToolExecutorSearchFlights:
    def test_search_flights_returns_markup_prices(self, executor, mock_amadeus, sample_raw_flights):
        mock_amadeus.search_flights.return_value = sample_raw_flights

        result_str = executor.execute("search_flights", {
            "origin": "JFK", "destination": "LAX", "departure_date": "2026-03-15",
        })
        result = json.loads(result_str)

        assert result["count"] == 2
        # First flight: actual=350, markup=385
        assert result["flights"][0]["price"] == 385.0
        assert result["flights"][1]["price"] == _markup(425.0)

    def test_search_flights_stores_state(self, executor, mock_amadeus, sample_raw_flights):
        mock_amadeus.search_flights.return_value = sample_raw_flights

        executor.execute("search_flights", {
            "origin": "JFK", "destination": "LAX", "departure_date": "2026-03-15",
        })

        assert len(executor.last_flights) == 2
        # Internal state has actual prices
        assert executor.last_flights[0].actual_price == 350.0
        assert executor.last_flights[0].markup_price == 385.0

    def test_search_flights_empty(self, executor, mock_amadeus):
        result = json.loads(executor.execute("search_flights", {
            "origin": "JFK", "destination": "LAX", "departure_date": "2026-03-15",
        }))
        assert result["count"] == 0
        assert result["flights"] == []

    def test_search_flights_passes_params(self, executor, mock_amadeus):
        executor.execute("search_flights", {
            "origin": "JFK", "destination": "LAX", "departure_date": "2026-03-15",
            "cabin_class": "BUSINESS", "passengers": 2, "non_stop": True,
        })
        mock_amadeus.search_flights.assert_called_once_with(
            origin="JFK", destination="LAX", departure_date="2026-03-15",
            return_date=None, passengers=2, cabin_class="BUSINESS",
            max_price=None, non_stop=True,
        )


class TestToolExecutorSearchHotels:
    def test_search_hotels_returns_markup(self, executor, mock_amadeus, sample_raw_hotels):
        hotels, offers = sample_raw_hotels
        mock_amadeus.search_hotels_by_city.return_value = hotels
        mock_amadeus.search_hotel_offers.return_value = offers

        result = json.loads(executor.execute("search_hotels", {
            "city_code": "PAR", "check_in": "2026-04-10", "check_out": "2026-04-14",
        }))

        assert result["count"] == 1
        assert result["hotels"][0]["total_price"] == _markup(800.0)
        assert result["hotels"][0]["nights"] == 4

    def test_search_hotels_no_results(self, executor, mock_amadeus):
        result = json.loads(executor.execute("search_hotels", {
            "city_code": "XXX", "check_in": "2026-04-10", "check_out": "2026-04-14",
        }))
        assert result["count"] == 0


class TestToolExecutorActivitiesAndPOIs:
    def test_search_activities(self, executor, mock_amadeus, sample_raw_activities):
        mock_amadeus.get_city_coordinates.return_value = (48.85, 2.35)
        mock_amadeus.search_activities.return_value = sample_raw_activities

        result = json.loads(executor.execute("search_activities", {"city_code": "PAR"}))
        assert result["count"] == 1
        assert result["activities"][0]["price"] == _markup(45.0)

    def test_search_activities_no_coords(self, executor, mock_amadeus):
        result = json.loads(executor.execute("search_activities", {"city_code": "XXX"}))
        assert result["count"] == 0

    def test_search_pois(self, executor, mock_amadeus, sample_raw_pois):
        mock_amadeus.get_city_coordinates.return_value = (48.85, 2.35)
        mock_amadeus.search_pois.return_value = sample_raw_pois

        result = json.loads(executor.execute("search_points_of_interest", {"city_code": "PAR"}))
        assert result["count"] == 1
        assert result["points_of_interest"][0]["name"] == "Louvre Museum"


class TestToolExecutorResolveLocation:
    def test_resolve_location(self, executor, mock_amadeus, sample_locations):
        mock_amadeus.search_locations.return_value = sample_locations

        result = json.loads(executor.execute("resolve_location", {"keyword": "New York"}))
        assert len(result["locations"]) == 2
        assert result["locations"][0]["iata"] == "JFK"


class TestToolExecutorBookFlight:
    def test_book_flight(self, executor, mock_amadeus, sample_raw_flights):
        mock_amadeus.search_flights.return_value = sample_raw_flights
        executor.execute("search_flights", {
            "origin": "JFK", "destination": "LAX", "departure_date": "2026-03-15",
        })

        result = json.loads(executor.execute("book_flight", {
            "flight_index": 0, "traveler_name": "John Doe", "traveler_email": "john@example.com",
        }))

        assert result["status"] == "confirmed"
        assert result["price"] == 385.0
        assert "VYG-F-" in result["booking_id"] or "API-" in result["booking_id"]
        assert len(executor.bookings) == 1

    def test_book_flight_generates_ticket(self, executor, mock_amadeus, sample_raw_flights):
        mock_amadeus.search_flights.return_value = sample_raw_flights
        executor.execute("search_flights", {
            "origin": "JFK", "destination": "LAX", "departure_date": "2026-03-15",
        })

        result = json.loads(executor.execute("book_flight", {
            "flight_index": 0, "traveler_name": "Jane Doe", "traveler_email": "jane@x.com",
        }))

        ticket_path = result["ticket_file"]
        assert os.path.exists(ticket_path)
        with open(ticket_path) as f:
            content = f.read()
        assert "VOYAGER TRAVEL" in content
        assert "Jane Doe" in content
        assert "$385.00" in content

    def test_book_flight_invalid_index(self, executor):
        result = json.loads(executor.execute("book_flight", {
            "flight_index": 99, "traveler_name": "X", "traveler_email": "x@x.com",
        }))
        assert "error" in result

    def test_booking_tracks_actual_price(self, executor, mock_amadeus, sample_raw_flights):
        mock_amadeus.search_flights.return_value = sample_raw_flights
        executor.execute("search_flights", {
            "origin": "JFK", "destination": "LAX", "departure_date": "2026-03-15",
        })
        executor.execute("book_flight", {
            "flight_index": 0, "traveler_name": "X", "traveler_email": "x@x.com",
        })

        booking = executor.bookings[0]
        assert booking.actual_price == 350.0
        assert booking.markup_price == 385.0


class TestToolExecutorBookHotel:
    def test_book_hotel(self, executor, mock_amadeus, sample_raw_hotels):
        hotels, offers = sample_raw_hotels
        mock_amadeus.search_hotels_by_city.return_value = hotels
        mock_amadeus.search_hotel_offers.return_value = offers
        executor.execute("search_hotels", {
            "city_code": "PAR", "check_in": "2026-04-10", "check_out": "2026-04-14",
        })

        result = json.loads(executor.execute("book_hotel", {
            "hotel_index": 0, "traveler_name": "Jane Doe", "traveler_email": "jane@x.com",
        }))

        assert result["status"] == "confirmed"
        assert result["price"] == _markup(800.0)
        assert os.path.exists(result["voucher_file"])


class TestToolExecutorPresentation:
    def test_create_presentation(self, executor, mock_amadeus, sample_raw_flights):
        mock_amadeus.search_flights.return_value = sample_raw_flights
        executor.execute("search_flights", {
            "origin": "JFK", "destination": "LAX", "departure_date": "2026-03-15",
        })

        result = json.loads(executor.execute("create_trip_presentation", {
            "trip_title": "LA Getaway",
            "traveler_name": "John",
            "destination": "Los Angeles",
            "departure_date": "2026-03-15",
            "return_date": "2026-03-22",
        }))

        assert os.path.exists(result["presentation_file"])
        with open(result["presentation_file"]) as f:
            content = f.read()
        assert "LA Getaway" in content
        assert "John" in content


class TestToolExecutorUnknownTool:
    def test_unknown_tool(self, executor):
        result = json.loads(executor.execute("nonexistent", {}))
        assert "error" in result
