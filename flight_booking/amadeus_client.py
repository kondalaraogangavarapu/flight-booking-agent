"""Amadeus REST API client for flights, hotels, activities, and transfers.

Uses the Amadeus Self-Service APIs directly via requests.
API docs: https://developers.amadeus.com/self-service

This module defines its own internal data types for raw API responses.
The tools module converts these into agent-level models with markup pricing.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import requests

# ---------------------------------------------------------------------------
# Internal data types (raw API layer — no markup)
# ---------------------------------------------------------------------------

@dataclass
class RawFlight:
    flight_number: str
    airline: str
    airline_code: str
    origin: str
    destination: str
    departure: datetime
    arrival: datetime
    price: float
    currency: str
    cabin_class: str
    stops: int
    available_seats: int
    layover_airports: list[str] = field(default_factory=list)
    raw_offer: dict[str, Any] = field(default_factory=dict, repr=False)

    def duration_display(self) -> str:
        delta = self.arrival - self.departure
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes = remainder // 60
        return f"{hours}h {minutes}m"


@dataclass
class RawHotel:
    hotel_id: str
    name: str
    chain_code: str
    city_code: str
    latitude: float
    longitude: float
    address: str


@dataclass
class RawHotelOffer:
    offer_id: str
    hotel: RawHotel
    check_in: str
    check_out: str
    room_type: str
    room_description: str
    beds: int
    bed_type: str
    board_type: str
    price: float
    currency: str
    cancellation_info: str
    raw_offer: dict[str, Any] = field(default_factory=dict, repr=False)


@dataclass
class RawPointOfInterest:
    poi_id: str
    name: str
    category: str
    latitude: float
    longitude: float
    tags: list[str] = field(default_factory=list)
    rank: int = 0


@dataclass
class RawActivity:
    activity_id: str
    name: str
    description: str
    price: float
    currency: str
    rating: str
    booking_link: str
    picture_url: str = ""
    latitude: float = 0
    longitude: float = 0


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE_URL = "https://test.api.amadeus.com"
PRODUCTION_URL = "https://api.amadeus.com"

AIRLINE_NAMES: dict[str, str] = {
    "AA": "American Airlines", "DL": "Delta Air Lines", "UA": "United Airlines",
    "WN": "Southwest Airlines", "B6": "JetBlue Airways", "AS": "Alaska Airlines",
    "NK": "Spirit Airlines", "F9": "Frontier Airlines", "BA": "British Airways",
    "AF": "Air France", "LH": "Lufthansa", "EK": "Emirates",
    "SQ": "Singapore Airlines", "JL": "Japan Airlines", "NH": "ANA",
    "QF": "Qantas", "AC": "Air Canada", "KL": "KLM",
    "LX": "Swiss International", "IB": "Iberia", "AY": "Finnair",
    "TK": "Turkish Airlines", "QR": "Qatar Airways", "EY": "Etihad Airways",
    "CX": "Cathay Pacific", "AI": "Air India", "MH": "Malaysia Airlines",
    "TG": "Thai Airways", "OZ": "Asiana Airlines", "KE": "Korean Air",
    "VS": "Virgin Atlantic", "HA": "Hawaiian Airlines", "WS": "WestJet",
}


class FlightSearchError(Exception):
    """Raised when an API call fails."""


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class AmadeusFlightClient:
    """Wraps the Amadeus REST API for travel search and booking."""

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        use_production: bool = False,
    ) -> None:
        self.client_id = client_id or os.environ.get("AMADEUS_CLIENT_ID", "")
        self.client_secret = client_secret or os.environ.get("AMADEUS_CLIENT_SECRET", "")
        self.base_url = PRODUCTION_URL if use_production else BASE_URL
        self._token: str | None = None
        self._token_expires: float = 0

    # --- Auth ---

    def _get_token(self) -> str:
        if self._token and time.time() < self._token_expires:
            return self._token
        resp = requests.post(
            f"{self.base_url}/v1/security/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
        if resp.status_code != 200:
            raise FlightSearchError(f"Auth failed ({resp.status_code}): {resp.text}")
        data = resp.json()
        self._token = data["access_token"]
        self._token_expires = time.time() + data.get("expires_in", 1799) - 60
        return self._token

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._get_token()}"}

    # --- Location search ---

    def search_locations(self, keyword: str) -> list[dict[str, str]]:
        resp = requests.get(
            f"{self.base_url}/v1/reference-data/locations",
            params={"keyword": keyword, "subType": "CITY,AIRPORT"},
            headers=self._headers(),
            timeout=30,
        )
        if resp.status_code != 200:
            return []
        results = []
        for loc in resp.json().get("data", []):
            results.append({
                "iata": loc.get("iataCode", ""),
                "name": loc.get("name", ""),
                "city": loc.get("address", {}).get("cityName", ""),
                "country": loc.get("address", {}).get("countryCode", ""),
                "type": loc.get("subType", ""),
            })
        return results

    # =========================================================================
    # FLIGHTS
    # =========================================================================

    def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: str | None = None,
        passengers: int = 1,
        cabin_class: str = "ECONOMY",
        max_price: float | None = None,
        non_stop: bool = False,
    ) -> list[RawFlight]:
        params: dict[str, Any] = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": departure_date,
            "adults": passengers,
            "travelClass": cabin_class,
            "currencyCode": "USD",
            "max": 50,
        }
        if return_date:
            params["returnDate"] = return_date
        if max_price is not None:
            params["maxPrice"] = int(max_price)
        if non_stop:
            params["nonStop"] = "true"

        resp = requests.get(
            f"{self.base_url}/v2/shopping/flight-offers",
            params=params, headers=self._headers(), timeout=30,
        )
        if resp.status_code != 200:
            raise FlightSearchError(
                f"Flight search failed ({resp.status_code}): {resp.json().get('errors', resp.text)}"
            )
        body = resp.json()
        carriers = body.get("dictionaries", {}).get("carriers", {})
        return self._parse_flight_offers(body.get("data", []), carriers, cabin_class)

    def create_flight_booking(
        self, raw_offer: dict[str, Any], name: str, email: str, phone: str = "+1234567890",
    ) -> dict[str, Any]:
        parts = name.strip().split()
        first = parts[0] if parts else "UNKNOWN"
        last = " ".join(parts[1:]) if len(parts) > 1 else "UNKNOWN"
        body = {
            "data": {
                "type": "flight-order",
                "flightOffers": [raw_offer],
                "travelers": [{
                    "id": "1", "dateOfBirth": "1990-01-01",
                    "name": {"firstName": first.upper(), "lastName": last.upper()},
                    "gender": "MALE",
                    "contact": {
                        "emailAddress": email,
                        "phones": [{"deviceType": "MOBILE", "countryCallingCode": "1", "number": phone.lstrip("+1")}],
                    },
                }],
            }
        }
        resp = requests.post(
            f"{self.base_url}/v1/booking/flight-orders",
            json=body, headers={**self._headers(), "Content-Type": "application/json"}, timeout=30,
        )
        if resp.status_code not in (200, 201):
            raise FlightSearchError(f"Flight booking failed ({resp.status_code})")
        return resp.json().get("data", {})

    def _parse_flight_offers(
        self, offers: list[dict], carriers: dict[str, str], cabin_class: str,
    ) -> list[RawFlight]:
        flights: list[RawFlight] = []
        for offer in offers:
            price = float(offer["price"]["grandTotal"])
            currency = offer["price"]["currency"]
            seats = offer.get("numberOfBookableSeats", 9)
            for itinerary in offer["itineraries"]:
                segments = itinerary["segments"]
                first_seg, last_seg = segments[0], segments[-1]
                cc = first_seg["carrierCode"]
                flights.append(RawFlight(
                    flight_number=f"{cc}{first_seg['number']}",
                    airline=carriers.get(cc, AIRLINE_NAMES.get(cc, cc)),
                    airline_code=cc,
                    origin=first_seg["departure"]["iataCode"],
                    destination=last_seg["arrival"]["iataCode"],
                    departure=datetime.fromisoformat(first_seg["departure"]["at"]),
                    arrival=datetime.fromisoformat(last_seg["arrival"]["at"]),
                    price=price, currency=currency,
                    cabin_class=cabin_class,
                    stops=len(segments) - 1,
                    available_seats=seats,
                    layover_airports=[s["arrival"]["iataCode"] for s in segments[:-1]],
                    raw_offer=offer,
                ))
        return flights

    # =========================================================================
    # HOTELS
    # =========================================================================

    def search_hotels_by_city(self, city_code: str, ratings: str = "") -> list[RawHotel]:
        params: dict[str, Any] = {"cityCode": city_code}
        if ratings:
            params["ratings"] = ratings
        resp = requests.get(
            f"{self.base_url}/v1/reference-data/locations/hotels/by-city",
            params=params, headers=self._headers(), timeout=30,
        )
        if resp.status_code != 200:
            return []
        hotels = []
        for h in resp.json().get("data", [])[:20]:
            geo = h.get("geoCode", {})
            hotels.append(RawHotel(
                hotel_id=h.get("hotelId", ""),
                name=h.get("name", ""),
                chain_code=h.get("chainCode", ""),
                city_code=h.get("iataCode", city_code),
                latitude=geo.get("latitude", 0),
                longitude=geo.get("longitude", 0),
                address=h.get("address", {}).get("countryCode", ""),
            ))
        return hotels

    def search_hotel_offers(
        self, hotel_ids: list[str], check_in: str, check_out: str, adults: int = 1, rooms: int = 1,
    ) -> list[RawHotelOffer]:
        if not hotel_ids:
            return []
        params = {
            "hotelIds": ",".join(hotel_ids[:20]),
            "adults": adults,
            "checkInDate": check_in,
            "checkOutDate": check_out,
            "roomQuantity": rooms,
            "currency": "USD",
            "bestRateOnly": "true",
        }
        resp = requests.get(
            f"{self.base_url}/v3/shopping/hotel-offers",
            params=params, headers=self._headers(), timeout=30,
        )
        if resp.status_code != 200:
            return []
        return self._parse_hotel_offers(resp.json().get("data", []))

    def _parse_hotel_offers(self, data: list[dict]) -> list[RawHotelOffer]:
        results: list[RawHotelOffer] = []
        for entry in data:
            if not entry.get("available"):
                continue
            hotel_data = entry.get("hotel", {})
            geo = hotel_data.get("geoCode") or {}
            hotel = RawHotel(
                hotel_id=hotel_data.get("hotelId", ""),
                name=hotel_data.get("name", ""),
                chain_code=hotel_data.get("chainCode", ""),
                city_code=hotel_data.get("cityCode", ""),
                latitude=geo.get("latitude", 0),
                longitude=geo.get("longitude", 0),
                address=hotel_data.get("address", {}).get("countryCode", "") if isinstance(hotel_data.get("address"), dict) else "",
            )
            for offer in entry.get("offers", []):
                room = offer.get("room", {})
                type_est = room.get("typeEstimated", {})
                price_data = offer.get("price", {})
                cancel = offer.get("policies", {}).get("cancellation", {})
                cancel_info = cancel.get("description", {}).get("text", "") if isinstance(cancel.get("description"), dict) else ""
                if not cancel_info and cancel.get("deadline"):
                    cancel_info = f"Free cancellation before {cancel['deadline']}"
                results.append(RawHotelOffer(
                    offer_id=offer.get("id", ""),
                    hotel=hotel,
                    check_in=offer.get("checkInDate", ""),
                    check_out=offer.get("checkOutDate", ""),
                    room_type=type_est.get("category", room.get("type", "")),
                    room_description=room.get("description", {}).get("text", "") if isinstance(room.get("description"), dict) else "",
                    beds=type_est.get("beds", 1),
                    bed_type=type_est.get("bedType", ""),
                    board_type=offer.get("boardType", "ROOM_ONLY"),
                    price=float(price_data.get("total", price_data.get("base", "0"))),
                    currency=price_data.get("currency", "USD"),
                    cancellation_info=cancel_info,
                    raw_offer=offer,
                ))
        return results

    # =========================================================================
    # POINTS OF INTEREST
    # =========================================================================

    def search_pois(self, latitude: float, longitude: float, categories: str = "") -> list[RawPointOfInterest]:
        params: dict[str, Any] = {"latitude": latitude, "longitude": longitude}
        if categories:
            params["categories"] = categories
        resp = requests.get(
            f"{self.base_url}/v1/reference-data/locations/pois",
            params=params, headers=self._headers(), timeout=30,
        )
        if resp.status_code != 200:
            return []
        pois = []
        for p in resp.json().get("data", [])[:15]:
            geo = p.get("geoCode", {})
            pois.append(RawPointOfInterest(
                poi_id=p.get("id", ""),
                name=p.get("name", ""),
                category=p.get("category", ""),
                latitude=geo.get("latitude", 0),
                longitude=geo.get("longitude", 0),
                tags=p.get("tags", []),
                rank=p.get("rank", 0),
            ))
        return pois

    # =========================================================================
    # TOURS & ACTIVITIES
    # =========================================================================

    def search_activities(self, latitude: float, longitude: float) -> list[RawActivity]:
        resp = requests.get(
            f"{self.base_url}/v1/shopping/activities",
            params={"latitude": latitude, "longitude": longitude},
            headers=self._headers(), timeout=30,
        )
        if resp.status_code != 200:
            return []
        activities = []
        for a in resp.json().get("data", [])[:10]:
            price_data = a.get("price", {})
            activities.append(RawActivity(
                activity_id=a.get("id", ""),
                name=a.get("name", ""),
                description=a.get("shortDescription", ""),
                price=float(price_data.get("amount", "0")),
                currency=price_data.get("currencyCode", "USD"),
                rating=a.get("rating", ""),
                booking_link=a.get("bookingLink", ""),
                picture_url=(a.get("pictures", [""])[0] if a.get("pictures") else ""),
                latitude=a.get("geoCode", {}).get("latitude", 0),
                longitude=a.get("geoCode", {}).get("longitude", 0),
            ))
        return activities

    # =========================================================================
    # CITY COORDINATES
    # =========================================================================

    def get_city_coordinates(self, city_code: str) -> tuple[float, float] | None:
        """Get lat/lon for a city code. Returns (lat, lon) or None."""
        resp = requests.get(
            f"{self.base_url}/v1/reference-data/locations",
            params={"keyword": city_code, "subType": "CITY"},
            headers=self._headers(), timeout=30,
        )
        if resp.status_code != 200:
            return None
        data = resp.json().get("data", [])
        for loc in data:
            geo = loc.get("geoCode", {})
            if geo.get("latitude") and geo.get("longitude"):
                return (geo["latitude"], geo["longitude"])
        return None
