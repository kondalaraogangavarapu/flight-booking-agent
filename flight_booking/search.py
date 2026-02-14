"""Flight search engine wrapping the Amadeus API with filtering and sorting."""

from __future__ import annotations

from .amadeus_client import AmadeusFlightClient, FlightSearchError
from .models import Flight, SearchCriteria


class FlightSearchEngine:
    """Searches, filters, and ranks flights from the Amadeus API."""

    def __init__(self, client: AmadeusFlightClient | None = None) -> None:
        self.client = client or AmadeusFlightClient()

    def search(self, criteria: SearchCriteria) -> list[Flight]:
        """Search for flights and apply local filters/preferences."""
        try:
            flights = self.client.search_flights(criteria)
        except FlightSearchError:
            return []

        return self._apply_filters(flights, criteria)

    def resolve_location(self, keyword: str) -> list[dict[str, str]]:
        """Resolve a city/airport keyword to IATA codes via the Amadeus API."""
        return self.client.search_locations(keyword)

    def _apply_filters(self, flights: list[Flight], criteria: SearchCriteria) -> list[Flight]:
        """Apply user preference filters on top of API results."""
        filtered = list(flights)

        if criteria.preferred_airline:
            airline_lower = criteria.preferred_airline.lower()
            preferred = [f for f in filtered if airline_lower in f.airline.lower()]
            others = [f for f in filtered if airline_lower not in f.airline.lower()]
            filtered = preferred + others

        if criteria.preferred_time:
            filtered = self._sort_by_time_preference(filtered, criteria.preferred_time)

        return filtered

    def _sort_by_time_preference(self, flights: list[Flight], preference: str) -> list[Flight]:
        """Sort flights by time-of-day preference."""
        ranges = {
            "morning": (5, 12),
            "afternoon": (12, 17),
            "evening": (17, 21),
            "night": (21, 24),
            "red-eye": (21, 6),
        }
        start, end = ranges.get(preference, (0, 24))

        def score(f: Flight) -> int:
            hour = f.departure.hour
            if start <= end:
                return 0 if start <= hour < end else 1
            return 0 if hour >= start or hour < end else 1

        return sorted(flights, key=score)

    @staticmethod
    def sort_by_price(flights: list[Flight]) -> list[Flight]:
        return sorted(flights, key=lambda f: f.price)

    @staticmethod
    def sort_by_duration(flights: list[Flight]) -> list[Flight]:
        return sorted(flights, key=lambda f: f.duration)

    @staticmethod
    def sort_by_departure(flights: list[Flight]) -> list[Flight]:
        return sorted(flights, key=lambda f: f.departure)

    @staticmethod
    def get_best_value(flights: list[Flight], top_n: int = 3) -> list[Flight]:
        """Return the best-value flights balancing price and duration."""
        if not flights:
            return []

        prices = [f.price for f in flights]
        durations = [f.duration_hours for f in flights]
        min_price, max_price = min(prices), max(prices)
        min_dur, max_dur = min(durations), max(durations)

        price_range = max_price - min_price if max_price > min_price else 1
        dur_range = max_dur - min_dur if max_dur > min_dur else 1

        def value_score(f: Flight) -> float:
            price_norm = (f.price - min_price) / price_range
            dur_norm = (f.duration_hours - min_dur) / dur_range
            return price_norm * 0.6 + dur_norm * 0.4

        scored = sorted(flights, key=value_score)
        return scored[:top_n]
