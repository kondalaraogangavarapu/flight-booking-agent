"""Data models for the flight booking agent."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


class CabinClass(Enum):
    ECONOMY = "ECONOMY"
    PREMIUM_ECONOMY = "PREMIUM_ECONOMY"
    BUSINESS = "BUSINESS"
    FIRST = "FIRST"

    def display(self) -> str:
        return self.value.replace("_", " ").title()

    def amadeus_code(self) -> str:
        """Return the Amadeus API travel class code."""
        return self.value


class TripType(Enum):
    ONE_WAY = "one_way"
    ROUND_TRIP = "round_trip"


@dataclass
class Flight:
    flight_number: str
    airline: str
    airline_code: str
    origin: str  # IATA code
    destination: str  # IATA code
    departure: datetime
    arrival: datetime
    price: float
    currency: str
    cabin_class: CabinClass
    stops: int
    available_seats: int
    layover_airports: list[str] = field(default_factory=list)
    raw_offer: dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def duration(self) -> timedelta:
        return self.arrival - self.departure

    @property
    def duration_hours(self) -> float:
        return self.duration.total_seconds() / 3600

    def duration_display(self) -> str:
        total_minutes = int(self.duration.total_seconds() // 60)
        hours, minutes = divmod(total_minutes, 60)
        return f"{hours}h {minutes}m"

    def stops_display(self) -> str:
        if self.stops == 0:
            return "Non-stop"
        if self.stops == 1:
            label = f"1 stop ({self.layover_airports[0]})" if self.layover_airports else "1 stop"
            return label
        airports = ", ".join(self.layover_airports[: self.stops])
        return f"{self.stops} stops ({airports})" if self.layover_airports else f"{self.stops} stops"


@dataclass
class SearchCriteria:
    origin: str | None = None  # IATA code
    destination: str | None = None  # IATA code
    departure_date: str | None = None  # YYYY-MM-DD
    return_date: str | None = None  # YYYY-MM-DD
    passengers: int = 1
    cabin_class: CabinClass = CabinClass.ECONOMY
    trip_type: TripType = TripType.ROUND_TRIP
    max_price: float | None = None
    max_stops: int | None = None
    preferred_airline: str | None = None
    preferred_time: str | None = None  # "morning", "afternoon", "evening", "night"

    def is_complete(self) -> bool:
        """Check if we have enough info to search."""
        return all([self.origin, self.destination, self.departure_date])


@dataclass
class Booking:
    booking_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8].upper())
    outbound_flight: Flight | None = None
    return_flight: Flight | None = None
    passengers: int = 1
    trip_type: TripType = TripType.ROUND_TRIP
    total_price: float = 0.0
    currency: str = "USD"
    passenger_name: str = ""
    passenger_email: str = ""
    confirmed: bool = False

    def calculate_total(self) -> float:
        total = 0.0
        if self.outbound_flight:
            total += self.outbound_flight.price
            self.currency = self.outbound_flight.currency
        if self.return_flight:
            total += self.return_flight.price
        self.total_price = total
        return total
