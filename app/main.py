import asyncio
import dataclasses
import logging
import signal
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr

from app.config import settings
from app.flights import SAMPLE_FLIGHTS, get_flight, search_flights
from app.models import AgentMessage, AgentResponse

logging.basicConfig(level=settings.LOG_LEVEL.upper())
logger = logging.getLogger(__name__)

shutdown_event = asyncio.Event()
startup_time: float = 0.0


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and graceful shutdown."""
    global startup_time
    startup_time = time.monotonic()

    loop = asyncio.get_running_loop()

    def _signal_handler(sig: signal.Signals) -> None:
        logger.info("Received %s, initiating graceful shutdown...", sig.name)
        shutdown_event.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _signal_handler, sig)

    logger.info("Application startup complete")
    yield
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# In-memory bookings store (replace with a database in production)
# ---------------------------------------------------------------------------
bookings: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------
class SearchQuery(BaseModel):
    origin: str
    destination: str
    departure_date: str  # YYYY-MM-DD
    passengers: int = 1


class BookingCreate(BaseModel):
    flight_id: str
    passenger_name: str
    passenger_email: EmailStr


# ---------------------------------------------------------------------------
# Health & readiness
# ---------------------------------------------------------------------------
@app.get("/healthz")
def health_check():
    """Liveness probe: checks that the application process is responsive."""
    uptime = round(time.monotonic() - startup_time, 2) if startup_time else 0
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "uptime_seconds": uptime,
    }


@app.get("/readyz")
def readiness_check():
    """Readiness probe: checks that the application can serve traffic."""
    if shutdown_event.is_set():
        raise HTTPException(status_code=503, detail="Shutting down")
    try:
        if not SAMPLE_FLIGHTS:
            raise RuntimeError("Flight data store is empty")
        _ = get_flight("FL001")  # verify data store is accessible
    except Exception as exc:
        logger.error("Readiness check failed: %s", exc)
        raise HTTPException(status_code=503, detail="Not ready") from exc
    return {"status": "ready"}


# ---------------------------------------------------------------------------
# Flight search
# ---------------------------------------------------------------------------
@app.post("/api/v1/flights/search")
def search(query: SearchQuery):
    logger.info("Searching flights %s -> %s on %s", query.origin, query.destination, query.departure_date)
    results = search_flights(query.origin, query.destination, query.departure_date)
    return {
        "count": len(results),
        "flights": [dataclasses.asdict(f) for f in results],
    }


@app.get("/api/v1/flights/{flight_id}")
def flight_detail(flight_id: str):
    flight = get_flight(flight_id)
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")
    return dataclasses.asdict(flight)


# ---------------------------------------------------------------------------
# Bookings
# ---------------------------------------------------------------------------
@app.post("/api/v1/bookings", status_code=201)
def create_booking(body: BookingCreate):
    flight = get_flight(body.flight_id)
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")
    if flight.seats_available < 1:
        raise HTTPException(status_code=409, detail="No seats available")

    booking_id = str(uuid.uuid4())
    booking = {
        "booking_id": booking_id,
        "flight_id": body.flight_id,
        "passenger_name": body.passenger_name,
        "passenger_email": body.passenger_email,
        "status": "confirmed",
        "created_at": datetime.utcnow().isoformat(),
    }
    bookings[booking_id] = booking
    flight.seats_available -= 1
    logger.info("Booking %s created for flight %s", booking_id, body.flight_id)
    return booking


@app.get("/api/v1/bookings/{booking_id}")
def get_booking(booking_id: str):
    booking = bookings.get(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


# ---------------------------------------------------------------------------
# Conversational agent
# ---------------------------------------------------------------------------
@app.post("/api/v1/agent", response_model=AgentResponse, tags=["agent"])
def agent_chat(body: AgentMessage):
    """Send a natural-language message to the flight booking agent."""
    from app.agent import handle_message

    return handle_message(body.message)
