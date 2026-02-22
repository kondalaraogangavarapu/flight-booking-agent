from pydantic import BaseModel
from enum import Enum


class CabinClass(str, Enum):
    economy = "economy"
    business = "business"
    first = "first"


class FlightSearchRequest(BaseModel):
    origin: str
    destination: str
    date: str
    passengers: int = 1
    cabin_class: CabinClass = CabinClass.economy


class BookingRequest(BaseModel):
    flight_id: str
    passenger_name: str
    email: str
    passengers: int = 1


class Flight(BaseModel):
    flight_id: str
    airline: str
    origin: str
    destination: str
    departure: str
    arrival: str
    price: float
    currency: str = "USD"
    cabin_class: CabinClass
    seats_available: int


class Booking(BaseModel):
    booking_id: str
    flight_id: str
    passenger_name: str
    email: str
    passengers: int
    status: str
    total_price: float
    currency: str = "USD"
