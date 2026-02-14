"""Amadeus REST API client for searching and booking real flights.

Uses the Amadeus Self-Service APIs directly via requests (no SDK dependency).
API docs: https://developers.amadeus.com/self-service
"""

from __future__ import annotations

import os
import time
from datetime import datetime
from typing import Any

import requests

from .models import CabinClass, Flight, SearchCriteria

BASE_URL = "https://test.api.amadeus.com"  # test environment
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
    """Raised when a flight search or booking fails."""


class AmadeusFlightClient:
    """Wraps the Amadeus REST API for flight search, pricing, and booking."""

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

    def _get_token(self) -> str:
        """Obtain or refresh an OAuth2 access token."""
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

    # --- Flight search ---

    def search_flights(self, criteria: SearchCriteria) -> list[Flight]:
        """Search for flights using the Amadeus Flight Offers Search API."""
        if not criteria.is_complete():
            return []

        params: dict[str, Any] = {
            "originLocationCode": criteria.origin,
            "destinationLocationCode": criteria.destination,
            "departureDate": criteria.departure_date,
            "adults": criteria.passengers,
            "travelClass": criteria.cabin_class.amadeus_code(),
            "currencyCode": "USD",
            "max": 50,
        }
        if criteria.return_date:
            params["returnDate"] = criteria.return_date
        if criteria.max_price is not None:
            params["maxPrice"] = int(criteria.max_price)
        if criteria.max_stops is not None and criteria.max_stops == 0:
            params["nonStop"] = "true"

        resp = requests.get(
            f"{self.base_url}/v2/shopping/flight-offers",
            params=params,
            headers=self._headers(),
            timeout=30,
        )
        if resp.status_code != 200:
            raise FlightSearchError(
                f"Search failed ({resp.status_code}): {resp.json().get('errors', resp.text)}"
            )

        body = resp.json()
        carriers = body.get("dictionaries", {}).get("carriers", {})
        return self._parse_offers(body.get("data", []), carriers, criteria)

    def confirm_price(self, flight: Flight) -> Flight:
        """Confirm the latest price for a selected flight offer."""
        if not flight.raw_offer:
            return flight

        resp = requests.post(
            f"{self.base_url}/v1/shopping/flight-offers/pricing",
            json={"data": {"type": "flight-offers-pricing", "flightOffers": [flight.raw_offer]}},
            headers={**self._headers(), "Content-Type": "application/json"},
            timeout=30,
        )
        if resp.status_code == 200:
            offers = resp.json().get("data", {}).get("flightOffers", [])
            if offers:
                updated = offers[0]
                flight.price = float(updated["price"]["grandTotal"])
                flight.currency = updated["price"]["currency"]
                flight.raw_offer = updated
        return flight

    def create_booking(
        self,
        flight: Flight,
        passenger_name: str,
        passenger_email: str,
        passenger_phone: str = "+1234567890",
    ) -> dict[str, Any]:
        """Create a flight booking via the Amadeus Flight Create Orders API."""
        name_parts = passenger_name.strip().split()
        first_name = name_parts[0] if name_parts else "UNKNOWN"
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else "UNKNOWN"

        body = {
            "data": {
                "type": "flight-order",
                "flightOffers": [flight.raw_offer],
                "travelers": [
                    {
                        "id": "1",
                        "dateOfBirth": "1990-01-01",
                        "name": {"firstName": first_name.upper(), "lastName": last_name.upper()},
                        "gender": "MALE",
                        "contact": {
                            "emailAddress": passenger_email,
                            "phones": [
                                {
                                    "deviceType": "MOBILE",
                                    "countryCallingCode": "1",
                                    "number": passenger_phone.lstrip("+1"),
                                }
                            ],
                        },
                    }
                ],
            }
        }

        resp = requests.post(
            f"{self.base_url}/v1/booking/flight-orders",
            json=body,
            headers={**self._headers(), "Content-Type": "application/json"},
            timeout=30,
        )
        if resp.status_code not in (200, 201):
            raise FlightSearchError(
                f"Booking failed ({resp.status_code}): {resp.json().get('errors', resp.text)}"
            )
        return resp.json().get("data", {})

    # --- Location search ---

    def search_locations(self, keyword: str) -> list[dict[str, str]]:
        """Search for airport/city locations by keyword."""
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

    # --- Response parsing ---

    def _parse_offers(
        self,
        offers: list[dict[str, Any]],
        carriers: dict[str, str],
        criteria: SearchCriteria,
    ) -> list[Flight]:
        """Parse Amadeus flight offer responses into Flight objects."""
        flights: list[Flight] = []

        for offer in offers:
            price = float(offer["price"]["grandTotal"])
            currency = offer["price"]["currency"]
            seats = offer.get("numberOfBookableSeats", 9)

            for itinerary in offer["itineraries"]:
                segments = itinerary["segments"]
                first_seg = segments[0]
                last_seg = segments[-1]

                carrier_code = first_seg["carrierCode"]
                flight_num = f"{carrier_code}{first_seg['number']}"
                airline_name = carriers.get(
                    carrier_code, AIRLINE_NAMES.get(carrier_code, carrier_code)
                )

                departure = datetime.fromisoformat(first_seg["departure"]["at"])
                arrival = datetime.fromisoformat(last_seg["arrival"]["at"])

                origin_code = first_seg["departure"]["iataCode"]
                dest_code = last_seg["arrival"]["iataCode"]

                stops = len(segments) - 1
                layovers = [seg["arrival"]["iataCode"] for seg in segments[:-1]]

                cabin = criteria.cabin_class
                traveler_pricings = offer.get("travelerPricings", [])
                if traveler_pricings:
                    fare_details = traveler_pricings[0].get("fareDetailsBySegment", [])
                    if fare_details:
                        cabin_str = fare_details[0].get("cabin", "").upper()
                        try:
                            cabin = CabinClass(cabin_str)
                        except ValueError:
                            pass

                flights.append(Flight(
                    flight_number=flight_num,
                    airline=airline_name,
                    airline_code=carrier_code,
                    origin=origin_code,
                    destination=dest_code,
                    departure=departure,
                    arrival=arrival,
                    price=price,
                    currency=currency,
                    cabin_class=cabin,
                    stops=stops,
                    available_seats=seats,
                    layover_airports=layovers,
                    raw_offer=offer,
                ))

        return flights
