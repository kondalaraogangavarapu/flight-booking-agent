"""Tests for data models."""

from flight_booking.models import Activity, BookingRecord, Flight, HotelOffer, PointOfInterest


class TestFlight:
    def test_fields(self):
        f = Flight(
            flight_number="AA100", airline="American", origin="JFK",
            destination="LAX", departure="2026-03-15T08:00:00",
            arrival="2026-03-15T11:30:00", duration="3h 30m", stops=0,
            cabin_class="ECONOMY", actual_price=100.0, markup_price=110.0,
            currency="USD", seats_left=5,
        )
        assert f.markup_price == 110.0
        assert f.actual_price == 100.0
        assert f.flight_number == "AA100"

    def test_raw_offer_default(self):
        f = Flight(
            flight_number="X", airline="X", origin="A", destination="B",
            departure="", arrival="", duration="", stops=0, cabin_class="",
            actual_price=0, markup_price=0, currency="USD", seats_left=0,
        )
        assert f.raw_offer == {}


class TestHotelOffer:
    def test_fields(self):
        h = HotelOffer(
            hotel_name="Test Hotel", hotel_id="H1", offer_id="O1",
            room_type="DOUBLE", room_description="Nice room",
            board_type="BREAKFAST", check_in="2026-04-10",
            check_out="2026-04-14", nights=4, actual_price=400.0,
            markup_price=440.0, currency="USD", cancellation_info="Free",
        )
        assert h.nights == 4
        assert h.markup_price == 440.0


class TestBookingRecord:
    def test_defaults(self):
        r = BookingRecord(
            booking_id="VYG-1", booking_type="flight",
            traveler_name="John", traveler_email="j@x.com",
        )
        assert r.markup_price == 0.0
        assert r.actual_price == 0.0
        assert r.currency == "USD"


class TestActivity:
    def test_fields(self):
        a = Activity(
            name="Tour", description="Fun", actual_price=50.0,
            markup_price=55.0, currency="USD", rating="4.5",
            booking_link="https://example.com",
        )
        assert a.markup_price == 55.0


class TestPointOfInterest:
    def test_tags_default(self):
        p = PointOfInterest(name="Place", category="SIGHTS")
        assert p.tags == []
