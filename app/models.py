from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional
import uuid


@dataclass
class Flight:
    flight_id: str
    airline: str
    origin: str
    destination: str
    departure: datetime
    arrival: datetime
    price: float
    currency: str = "USD"
    seats_available: int = 0


@dataclass
class BookingRequest:
    flight_id: str
    passenger_name: str
    passenger_email: str


@dataclass
class Booking:
    booking_id: str
    flight_id: str
    passenger_name: str
    passenger_email: str
    status: str = "confirmed"
    created_at: str = ""

    def __post_init__(self):
        if not self.booking_id:
            self.booking_id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


@dataclass
class SearchRequest:
    origin: str
    destination: str
    departure_date: str
    passengers: int = 1
