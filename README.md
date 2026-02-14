# Flight Booking Agent

An interactive conversational flight booking agent that searches **real flights** from airlines via the [Amadeus API](https://developers.amadeus.com) and guides you through the booking process step by step.

## Features

- **Real flight data** — searches live flight offers from 400+ airlines via the Amadeus Flight Offers Search API
- **Conversational Q&A flow** — asks clarifying questions to narrow down the best options:
  - Origin and destination (with airport disambiguation when multiple matches exist)
  - Travel dates (departure + optional return)
  - Number of passengers
  - Cabin class (Economy, Premium Economy, Business, First)
  - Preferences: budget cap, non-stop only, preferred airline, departure time
- **Smart recommendations** — ranks flights by best value (60% price / 40% duration)
- **Interactive sorting** — sort results by price, duration, or departure time
- **Full booking flow** — select a flight, enter passenger details, confirm, and book via the API
- **Flexible date parsing** — understands `2026-03-15`, `March 15`, `tomorrow`, `next Friday`, `in 5 days`

## Quick Start

### 1. Get Amadeus API keys (free)

1. Sign up at [developers.amadeus.com](https://developers.amadeus.com)
2. Create a new app in the dashboard
3. Copy your **API Key** and **API Secret**

### 2. Set environment variables

```bash
export AMADEUS_CLIENT_ID='your_api_key'
export AMADEUS_CLIENT_SECRET='your_api_secret'
```

### 3. Install and run

```bash
pip install -e .
flight-agent
```

Or run directly:

```bash
pip install requests
python -m flight_booking.main
```

### 4. Example session

```
Welcome to FlightBooker! I'll help you find and book the best flights from real airlines.

Let's get started. Where would you like to fly from?
(Enter a city name or airport code, e.g., 'New York' or 'JFK')

> New York

Great, departing from NEW YORK (JFK).

Where would you like to fly to?

> London

I found multiple airports matching 'London'. Which one did you mean?

  1. LONDON - HEATHROW (GB) [LHR] (airport)
  2. LONDON - GATWICK (GB) [LGW] (airport)
  3. LONDON - STANSTED (GB) [STN] (airport)

Enter the number of your choice:

> 1

Flying to LONDON (LHR).

When would you like to depart?

> March 20

Departure date: March 20, 2026.

Is this a round trip? If so, when would you like to return?

> March 27

How many passengers will be traveling? (1-9)

> 1

Which cabin class do you prefer?
  1. Economy
  2. Premium Economy
  3. Business
  4. First Class

> 1

Do you have any preferences?
  - Maximum budget per person (e.g., '$500')
  - Non-stop only (e.g., 'non-stop' or 'direct')
  - Preferred airline (e.g., 'Delta')
  - Preferred departure time (e.g., 'morning', 'evening')

> $800 non-stop

I found 12 flights from JFK to LHR on 2026-03-20.

--- TOP RECOMMENDATIONS (Best Value) ---
  ...
```

## Project Structure

```
flight_booking/
  __init__.py
  main.py              # CLI entry point
  agent.py             # Conversational state machine
  amadeus_client.py    # Amadeus REST API client (auth, search, book)
  search.py            # Search engine with filtering and sorting
  models.py            # Data models (Flight, SearchCriteria, Booking)
tests/
  conftest.py          # Shared fixtures with mock API responses
  test_agent.py        # Agent conversation flow tests
  test_amadeus_client.py  # API response parsing tests
  test_search.py       # Search/filter/sort tests
  test_models.py       # Data model tests
```

## Running Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

All tests use mocked API responses — no real API calls or credentials needed for testing.

## API Details

This agent uses the following Amadeus Self-Service APIs:

| API | Endpoint | Purpose |
|-----|----------|---------|
| Flight Offers Search | `GET /v2/shopping/flight-offers` | Search for flights |
| Flight Offers Price | `POST /v1/shopping/flight-offers/pricing` | Confirm real-time pricing |
| Flight Create Orders | `POST /v1/booking/flight-orders` | Create a booking (PNR) |
| Airport & City Search | `GET /v1/reference-data/locations` | Resolve city/airport names |

The free test environment (`test.api.amadeus.com`) provides real flight data with 1,000-10,000 API calls/month. Set `use_production=True` in `AmadeusFlightClient` for production access.
