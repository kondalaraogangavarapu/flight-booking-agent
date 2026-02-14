"""Tests for flight booking data models."""

from datetime import datetime, timedelta

from flight_booking.models import Booking, CabinClass, Flight, SearchCriteria, TripType


def _make_flight(**kwargs):
    defaults = {
        "flight_number": "UA100",
        "airline": "United Airlines",
        "airline_code": "UA",
        "origin": "JFK",
        "destination": "LAX",
        "departure": datetime(2026, 5, 1, 8, 0),
        "arrival": datetime(2026, 5, 1, 13, 30),
        "price": 300.0,
        "currency": "USD",
        "cabin_class": CabinClass.ECONOMY,
        "stops": 0,
        "available_seats": 20,
    }
    defaults.update(kwargs)
    return Flight(**defaults)


class TestCabinClass:
    def test_display_economy(self):
        assert CabinClass.ECONOMY.display() == "Economy"

    def test_display_premium_economy(self):
        assert CabinClass.PREMIUM_ECONOMY.display() == "Premium Economy"

    def test_display_business(self):
        assert CabinClass.BUSINESS.display() == "Business"

    def test_display_first(self):
        assert CabinClass.FIRST.display() == "First"

    def test_amadeus_code(self):
        assert CabinClass.ECONOMY.amadeus_code() == "ECONOMY"
        assert CabinClass.BUSINESS.amadeus_code() == "BUSINESS"


class TestFlight:
    def test_duration(self):
        flight = _make_flight()
        assert flight.duration == timedelta(hours=5, minutes=30)

    def test_duration_hours(self):
        flight = _make_flight()
        assert flight.duration_hours == 5.5

    def test_duration_display(self):
        flight = _make_flight()
        assert flight.duration_display() == "5h 30m"

    def test_stops_display_nonstop(self):
        flight = _make_flight(stops=0)
        assert flight.stops_display() == "Non-stop"

    def test_stops_display_one_stop(self):
        flight = _make_flight(stops=1, layover_airports=["ORD"])
        assert flight.stops_display() == "1 stop (ORD)"

    def test_stops_display_two_stops(self):
        flight = _make_flight(stops=2, layover_airports=["ORD", "DEN"])
        assert flight.stops_display() == "2 stops (ORD, DEN)"


class TestSearchCriteria:
    def test_is_complete_missing_fields(self):
        criteria = SearchCriteria()
        assert criteria.is_complete() is False

    def test_is_complete_with_required_fields(self):
        criteria = SearchCriteria(origin="JFK", destination="LAX", departure_date="2026-05-01")
        assert criteria.is_complete() is True

    def test_defaults(self):
        criteria = SearchCriteria()
        assert criteria.passengers == 1
        assert criteria.cabin_class == CabinClass.ECONOMY
        assert criteria.trip_type == TripType.ROUND_TRIP


class TestBooking:
    def test_calculate_total_one_way(self):
        flight = _make_flight(price=300.0)
        booking = Booking(
            outbound_flight=flight,
            passengers=1,
            trip_type=TripType.ONE_WAY,
        )
        total = booking.calculate_total()
        assert total == 300.0

    def test_calculate_total_round_trip(self):
        outbound = _make_flight(price=300.0)
        ret = _make_flight(price=250.0)
        booking = Booking(
            outbound_flight=outbound,
            return_flight=ret,
            passengers=1,
            trip_type=TripType.ROUND_TRIP,
        )
        total = booking.calculate_total()
        assert total == 550.0

    def test_booking_id_generated(self):
        booking = Booking()
        assert len(booking.booking_id) == 8

    def test_currency_set_from_flight(self):
        flight = _make_flight(currency="EUR")
        booking = Booking(outbound_flight=flight)
        booking.calculate_total()
        assert booking.currency == "EUR"
