# Flight Booking Agent

A REST API service for searching and booking flights with a conversational AI agent, packaged as a Docker container. The agent endpoint is powered by Claude (falls back to keyword matching when no API key is configured).

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/healthz` | Health check |
| GET | `/readyz` | Readiness check |
| POST | `/api/v1/flights/search` | Search available flights |
| GET | `/api/v1/flights/{flight_id}` | Get flight details |
| POST | `/api/v1/bookings` | Create a booking |
| GET | `/api/v1/bookings/{booking_id}` | Get booking details |
| POST | `/api/v1/agent` | Chat with the booking agent |

## Running Locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
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
docker build -t flight-booking-agent:0.5.0 .
docker run -p 8000:8000 \
  -e SECRET_KEY=<your-secret> \
  -e ANTHROPIC_API_KEY=<your-key> \
  flight-booking-agent:0.5.0
```

The container uses gunicorn with uvicorn workers for production-grade process management. Configure workers via `WEB_CONCURRENCY`.

## Configuration

All configuration is via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_HOST` | `127.0.0.1` | Bind address (`0.0.0.0` in Docker) |
| `APP_PORT` | `8000` | Bind port |
| `LOG_LEVEL` | `info` | Logging level |
| `SECRET_KEY` | *(auto-generated)* | Application secret key (**must be set in production**) |
| `WEB_CONCURRENCY` | `2` | Number of gunicorn worker processes (Docker only) |
| `HEALTH_CHECK_TIMEOUT` | `5` | Health check HTTP timeout in seconds |
| `ANTHROPIC_API_KEY` | *(none)* | Enables LLM-powered conversational agent |

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

Chat with the agent:

```bash
curl -X POST http://localhost:8000/api/v1/agent \
  -H "Content-Type: application/json" \
  -d '{"message": "Find flights from JFK to LAX"}'
```
