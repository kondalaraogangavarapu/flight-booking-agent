"""Generate tickets and receipts for bookings."""

from __future__ import annotations

from .models import BookingRecord


def generate_flight_ticket(record: BookingRecord) -> str:
    """Generate a formatted flight ticket/receipt."""
    d = record.details
    return f"""\
================================================================================
                         VOYAGER TRAVEL - FLIGHT TICKET
================================================================================

  Booking Reference:  {record.booking_id}
  Date of Issue:      {record.timestamp[:10]}

  PASSENGER
  ---------
  Name:               {record.traveler_name}
  Email:              {record.traveler_email}

  FLIGHT DETAILS
  --------------
  Airline:            {d.get('airline', 'N/A')}
  Flight:             {d.get('flight_number', 'N/A')}
  Route:              {d.get('origin', '?')} -> {d.get('destination', '?')}
  Departure:          {d.get('departure', 'N/A')}
  Arrival:            {d.get('arrival', 'N/A')}
  Cabin:              {d.get('cabin_class', 'ECONOMY')}

  FARE
  ----
  Total Paid:         ${record.markup_price:,.2f} {record.currency}

================================================================================
  This is your official e-ticket receipt. Please present this document
  along with a valid photo ID at check-in.

  Thank you for booking with Voyager Travel!
================================================================================
"""


def generate_hotel_voucher(record: BookingRecord) -> str:
    """Generate a formatted hotel booking voucher/receipt."""
    d = record.details
    return f"""\
================================================================================
                        VOYAGER TRAVEL - HOTEL VOUCHER
================================================================================

  Booking Reference:  {record.booking_id}
  Date of Issue:      {record.timestamp[:10]}

  GUEST
  -----
  Name:               {record.traveler_name}
  Email:              {record.traveler_email}

  HOTEL DETAILS
  -------------
  Hotel:              {d.get('hotel_name', 'N/A')}
  Room:               {d.get('room_type', 'Standard')}
  Description:        {d.get('room_description', 'N/A')}
  Check-in:           {d.get('check_in', 'N/A')}
  Check-out:          {d.get('check_out', 'N/A')}
  Nights:             {d.get('nights', 'N/A')}

  PAYMENT
  -------
  Total Paid:         ${record.markup_price:,.2f} {record.currency}

================================================================================
  Present this voucher at the hotel reception upon arrival.
  Reservation is guaranteed. For changes or cancellations, contact us.

  Thank you for booking with Voyager Travel!
================================================================================
"""
