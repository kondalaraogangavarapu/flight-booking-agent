"""Tests for trip presentation generation."""

from flight_booking.models import Activity, BookingRecord, Flight, HotelOffer, PointOfInterest
from flight_booking.presentations import generate_trip_presentation


class TestTripPresentation:
    def test_basic_presentation(self):
        content = generate_trip_presentation(
            title="Paris Adventure",
            traveler_name="Alice",
            destination="Paris",
            departure_date="2026-04-10",
            return_date="2026-04-17",
        )
        assert "# Paris Adventure" in content
        assert "Alice" in content
        assert "Paris" in content
        assert "2026-04-10" in content
        assert "Voyager Travel" in content

    def test_with_trip_vibe(self):
        content = generate_trip_presentation(
            title="Romantic Escape",
            traveler_name="Bob",
            destination="Venice",
            departure_date="2026-05-01",
            return_date="2026-05-07",
            trip_vibe="romantic",
        )
        assert "romantic" in content

    def test_with_bookings(self):
        bookings = [
            BookingRecord(
                booking_id="VYG-F-001", booking_type="flight",
                traveler_name="Alice", traveler_email="a@x.com",
                details={"airline": "Air France", "flight_number": "AF100",
                         "origin": "JFK", "destination": "CDG",
                         "departure": "2026-04-10", "arrival": "2026-04-10"},
                markup_price=550.0, currency="USD",
            ),
            BookingRecord(
                booking_id="VYG-H-001", booking_type="hotel",
                traveler_name="Alice", traveler_email="a@x.com",
                details={"hotel_name": "Le Marais", "room_type": "DOUBLE",
                         "check_in": "2026-04-10", "check_out": "2026-04-17"},
                markup_price=1200.0, currency="USD",
            ),
        ]
        content = generate_trip_presentation(
            title="Paris Trip",
            traveler_name="Alice",
            destination="Paris",
            departure_date="2026-04-10",
            return_date="2026-04-17",
            bookings=bookings,
        )
        assert "Booked Flights" in content
        assert "Booked Hotels" in content
        assert "AF100" in content
        assert "Le Marais" in content
        assert "Trip Cost Summary" in content

    def test_with_activities_and_pois(self):
        activities = [
            Activity(name="Tour Eiffel", description="Great views",
                     actual_price=40.0, markup_price=44.0,
                     currency="USD", rating="4.8", booking_link=""),
        ]
        pois = [
            PointOfInterest(name="Louvre", category="SIGHTS", tags=["museum"]),
        ]
        content = generate_trip_presentation(
            title="Paris",
            traveler_name="X",
            destination="Paris",
            departure_date="2026-04-10",
            return_date="2026-04-17",
            activities=activities,
            pois=pois,
        )
        assert "Tour Eiffel" in content
        assert "Louvre" in content
        assert "Activities" in content
        assert "Points of Interest" in content
