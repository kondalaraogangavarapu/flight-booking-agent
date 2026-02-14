"""Generate trip presentation documents."""

from __future__ import annotations

from typing import Any

from .models import Activity, BookingRecord, Flight, HotelOffer, PointOfInterest


def generate_trip_presentation(
    title: str,
    traveler_name: str,
    destination: str,
    departure_date: str,
    return_date: str,
    travelers_count: int = 1,
    trip_vibe: str = "",
    notes: str = "",
    flights: list[Flight] | None = None,
    hotels: list[HotelOffer] | None = None,
    activities: list[Activity] | None = None,
    pois: list[PointOfInterest] | None = None,
    bookings: list[BookingRecord] | None = None,
) -> str:
    """Generate a markdown trip presentation document."""
    flights = flights or []
    hotels = hotels or []
    activities = activities or []
    pois = pois or []
    bookings = bookings or []

    lines = [
        f"# {title}",
        "",
        "---",
        "",
        f"**Prepared for:** {traveler_name}  ",
        f"**Destination:** {destination}  ",
        f"**Dates:** {departure_date} to {return_date}  ",
        f"**Travelers:** {travelers_count}  ",
    ]
    if trip_vibe:
        lines.append(f"**Trip Vibe:** {trip_vibe}  ")
    lines.append("")

    # Booked items
    flight_bookings = [b for b in bookings if b.booking_type == "flight"]
    hotel_bookings = [b for b in bookings if b.booking_type == "hotel"]

    if flight_bookings:
        lines.extend(["## Booked Flights", ""])
        for b in flight_bookings:
            d = b.details
            lines.extend([
                f"- **{d.get('airline', '')} {d.get('flight_number', '')}**  ",
                f"  {d.get('origin', '')} -> {d.get('destination', '')}  ",
                f"  Departure: {d.get('departure', '')}  ",
                f"  Arrival: {d.get('arrival', '')}  ",
                f"  Cabin: {d.get('cabin_class', '')}  ",
                f"  Price: ${b.markup_price:,.2f} {b.currency}  ",
                f"  Booking ID: `{b.booking_id}`  ",
                "",
            ])

    if hotel_bookings:
        lines.extend(["## Booked Hotels", ""])
        for b in hotel_bookings:
            d = b.details
            lines.extend([
                f"- **{d.get('hotel_name', '')}**  ",
                f"  Room: {d.get('room_type', '')}  ",
                f"  Check-in: {d.get('check_in', '')}  ",
                f"  Check-out: {d.get('check_out', '')}  ",
                f"  Nights: {d.get('nights', '')}  ",
                f"  Price: ${b.markup_price:,.2f} {b.currency}  ",
                f"  Booking ID: `{b.booking_id}`  ",
                "",
            ])

    # Available flights (not booked)
    if flights and not flight_bookings:
        lines.extend(["## Flight Options", ""])
        for i, f in enumerate(flights):
            lines.extend([
                f"### Option {i + 1}: {f.airline} {f.flight_number}",
                f"- Route: {f.origin} -> {f.destination}",
                f"- Departure: {f.departure}",
                f"- Arrival: {f.arrival}",
                f"- Duration: {f.duration}",
                f"- Stops: {f.stops}",
                f"- Cabin: {f.cabin_class}",
                f"- Price: ${f.markup_price:,.2f} {f.currency}",
                "",
            ])

    # Available hotels (not booked)
    if hotels and not hotel_bookings:
        lines.extend(["## Hotel Options", ""])
        for i, h in enumerate(hotels):
            lines.extend([
                f"### Option {i + 1}: {h.hotel_name}",
                f"- Room: {h.room_type}",
                f"- {h.check_in} to {h.check_out} ({h.nights} nights)",
                f"- Price: ${h.markup_price:,.2f} {h.currency}",
                "",
            ])

    if activities:
        lines.extend(["## Activities & Experiences", ""])
        for a in activities:
            price_str = f" - ${a.markup_price:,.2f} {a.currency}" if a.markup_price > 0 else ""
            rating_str = f" (Rating: {a.rating})" if a.rating else ""
            lines.append(f"- **{a.name}**{price_str}{rating_str}")
            if a.description:
                lines.append(f"  {a.description}")
            lines.append("")

    if pois:
        lines.extend(["## Points of Interest", ""])
        for p in pois:
            tags_str = f" ({', '.join(p.tags[:3])})" if p.tags else ""
            lines.append(f"- **{p.name}** [{p.category}]{tags_str}")
        lines.append("")

    # Cost summary
    total_cost = sum(b.markup_price for b in bookings)
    if total_cost > 0:
        lines.extend([
            "## Trip Cost Summary",
            "",
            "| Item | Cost |",
            "|------|------|",
        ])
        for b in bookings:
            label = b.details.get("airline", b.details.get("hotel_name", b.booking_type))
            lines.append(f"| {label} | ${b.markup_price:,.2f} {b.currency} |")
        lines.extend([
            f"| **Total** | **${total_cost:,.2f} USD** |",
            "",
        ])

    if notes:
        lines.extend(["## Notes", "", notes, ""])

    lines.extend([
        "---",
        "",
        "*Prepared by Voyager Travel. Bon voyage!*",
    ])

    return "\n".join(lines)
