# Flight Booking Agent

A REST API service for searching and booking flights, packaged as a Docker container.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/healthz` | Health check |
| GET | `/readyz` | Readiness check |
| POST | `/api/v1/flights/search` | Search available flights |
| GET | `/api/v1/flights/{flight_id}` | Get flight details |
| POST | `/api/v1/bookings` | Create a booking |
| GET | `/api/v1/bookings/{booking_id}` | Get booking details |

## Running Locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Development Setup

1. **Prerequisites**: Python 3.12 or later.

2. **Create a virtual environment and install dependencies**:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # On Windows: .venv\Scripts\activate
   pip install -r requirements-dev.txt
   ```

3. **Run the application in development mode** (with auto-reload):

   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

4. **Run tests**:

   ```bash
   pytest
   ```

5. **Code quality** (linting and formatting):

   ```bash
   black --check app/
   flake8 app/
   mypy app/
   ```

## Docker

Build and run:

```bash
docker build -t flight-booking-agent:0.3.0 .
docker run -p 8000:8000 -e SECRET_KEY=<your-secret> flight-booking-agent:0.3.0
```

## Configuration

All configuration is via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_HOST` | `0.0.0.0` | Bind address |
| `APP_PORT` | `8000` | Bind port |
| `LOG_LEVEL` | `info` | Logging level |
| `SECRET_KEY` | *(auto-generated)* | Application secret key (**must be set in production**) |

## Example Usage

Search flights:

```bash
curl -X POST http://localhost:8000/api/v1/flights/search \
  -H "Content-Type: application/json" \
  -d '{"origin": "JFK", "destination": "LAX", "departure_date": "2026-03-15"}'
```

Create a booking:

```bash
curl -X POST http://localhost:8000/api/v1/bookings \
  -H "Content-Type: application/json" \
  -d '{"flight_id": "FL001", "passenger_name": "Jane Doe", "passenger_email": "jane@example.com"}'
```
