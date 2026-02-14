"""Data models for the travel agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any


@dataclass
class Flight:
    flight_number: str
    airline: str
    origin: str
    destination: str
    departure: str
    arrival: str
    duration: str
    stops: int
    cabin_class: str
    actual_price: float  # what we pay
    markup_price: float  # what the traveler sees (actual + 10%)
    currency: str
    seats_left: int
    raw_offer: dict[str, Any] = field(default_factory=dict, repr=False)


@dataclass
class HotelOffer:
    hotel_name: str
    hotel_id: str
    offer_id: str
    room_type: str
    room_description: str
    board_type: str
    check_in: str
    check_out: str
    nights: int
    actual_price: float
    markup_price: float
    currency: str
    cancellation_info: str
    raw_offer: dict[str, Any] = field(default_factory=dict, repr=False)


@dataclass
class Activity:
    name: str
    description: str
    actual_price: float
    markup_price: float
    currency: str
    rating: str
    booking_link: str


@dataclass
class PointOfInterest:
    name: str
    category: str
    tags: list[str] = field(default_factory=list)


@dataclass
class BookingRecord:
    booking_id: str
    booking_type: str  # "flight", "hotel"
    traveler_name: str
    traveler_email: str
    details: dict[str, Any] = field(default_factory=dict)
    markup_price: float = 0.0
    actual_price: float = 0.0
    currency: str = "USD"
    timestamp: str = ""
