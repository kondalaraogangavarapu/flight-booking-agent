# Flight Booking Agent

A demo flight search and booking API built with FastAPI.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/flights` | List flights (with optional query filters) |
| POST | `/flights/search` | Search flights by origin, destination, date, cabin class |
| POST | `/bookings` | Create a booking |
| GET | `/bookings/{id}` | Retrieve a booking |
| DELETE | `/bookings/{id}` | Cancel a booking |

## Run locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Run with Docker

```bash
docker build -t flight-booking-agent .
docker run -p 8000:8000 flight-booking-agent
```

The API docs are available at `http://localhost:8000/docs`.
