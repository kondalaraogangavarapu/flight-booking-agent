"""Tests for receipt and voucher generation."""

from flight_booking.models import BookingRecord
from flight_booking.receipts import generate_flight_ticket, generate_hotel_voucher


class TestFlightTicket:
    def test_contains_booking_details(self):
        record = BookingRecord(
            booking_id="VYG-F-ABC123", booking_type="flight",
            traveler_name="Alice Smith", traveler_email="alice@example.com",
            details={
                "airline": "Delta Air Lines", "flight_number": "DL100",
                "origin": "JFK", "destination": "LAX",
                "departure": "2026-03-15T08:00", "arrival": "2026-03-15T11:30",
                "cabin_class": "ECONOMY",
            },
            markup_price=385.00, actual_price=350.00,
            currency="USD", timestamp="2026-03-01T10:00:00",
        )
        ticket = generate_flight_ticket(record)

        assert "VYG-F-ABC123" in ticket
        assert "Alice Smith" in ticket
        assert "alice@example.com" in ticket
        assert "Delta Air Lines" in ticket
        assert "DL100" in ticket
        assert "JFK" in ticket
        assert "LAX" in ticket
        assert "$385.00" in ticket
        assert "VOYAGER TRAVEL" in ticket

    def test_does_not_contain_actual_price(self):
        record = BookingRecord(
            booking_id="VYG-F-001", booking_type="flight",
            traveler_name="X", traveler_email="x@x.com",
            markup_price=110.0, actual_price=100.0,
            currency="USD", timestamp="2026-01-01",
        )
        ticket = generate_flight_ticket(record)
        assert "$100.00" not in ticket
        assert "$110.00" in ticket


class TestHotelVoucher:
    def test_contains_hotel_details(self):
        record = BookingRecord(
            booking_id="VYG-H-DEF456", booking_type="hotel",
            traveler_name="Bob Jones", traveler_email="bob@example.com",
            details={
                "hotel_name": "Hotel Le Marais", "room_type": "DOUBLE",
                "room_description": "Deluxe Room",
                "check_in": "2026-04-10", "check_out": "2026-04-14",
                "nights": 4,
            },
            markup_price=880.00, actual_price=800.00,
            currency="USD", timestamp="2026-03-01T10:00:00",
        )
        voucher = generate_hotel_voucher(record)

        assert "VYG-H-DEF456" in voucher
        assert "Bob Jones" in voucher
        assert "Hotel Le Marais" in voucher
        assert "DOUBLE" in voucher
        assert "$880.00" in voucher
        assert "VOYAGER TRAVEL" in voucher
