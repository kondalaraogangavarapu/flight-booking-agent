"""Flight Booking Agent API."""

import uuid
from fastapi import FastAPI, HTTPException

from app.models import (
    Booking,
    BookingRequest,
    CabinClass,
    Flight,
    FlightSearchRequest,
)
from app.flights import search_flights

app = FastAPI(
    title="Flight Booking Agent",
    description="A demo flight search and booking API.",
    version="1.0.0",
)

# In-memory booking store
bookings: dict[str, Booking] = {}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/flights/search", response_model=list[Flight])
def search(request: FlightSearchRequest):
    """Search for available flights."""
    results = search_flights(
        origin=request.origin,
        destination=request.destination,
        date=request.date,
        cabin_class=request.cabin_class,
    )
    return results


@app.get("/flights", response_model=list[Flight])
def list_flights(
    origin: str | None = None,
    destination: str | None = None,
    date: str | None = None,
    cabin_class: CabinClass | None = None,
):
    """List flights with optional filters."""
    return search_flights(origin, destination, date, cabin_class)


@app.post("/bookings", response_model=Booking)
def create_booking(request: BookingRequest):
    """Book a flight."""
    flights = search_flights()
    flight = next((f for f in flights if f.flight_id == request.flight_id), None)
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")
    if flight.seats_available < request.passengers:
        raise HTTPException(status_code=400, detail="Not enough seats available")

    booking_id = f"BK-{uuid.uuid4().hex[:8].upper()}"
    booking = Booking(
        booking_id=booking_id,
        flight_id=request.flight_id,
        passenger_name=request.passenger_name,
        email=request.email,
        passengers=request.passengers,
        status="confirmed",
        total_price=flight.price * request.passengers,
        currency=flight.currency,
    )
    bookings[booking_id] = booking
    return booking


@app.get("/bookings/{booking_id}", response_model=Booking)
def get_booking(booking_id: str):
    """Retrieve a booking by ID."""
    if booking_id not in bookings:
        raise HTTPException(status_code=404, detail="Booking not found")
    return bookings[booking_id]


@app.delete("/bookings/{booking_id}")
def cancel_booking(booking_id: str):
    """Cancel a booking."""
    if booking_id not in bookings:
        raise HTTPException(status_code=404, detail="Booking not found")
    bookings[booking_id].status = "cancelled"
    return {"detail": "Booking cancelled", "booking_id": booking_id}
