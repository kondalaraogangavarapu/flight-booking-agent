# ---- Build stage ----
FROM python:3.12-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- Runtime stage ----
FROM python:3.12-slim

LABEL org.opencontainers.image.title="flight-booking-agent" \
      org.opencontainers.image.version="0.2.0" \
      org.opencontainers.image.description="Flight booking agent REST API" \
      org.opencontainers.image.source="https://github.com/kondalaraogangavarapu/flight-booking-agent"

# Security: install upgrades and remove unnecessary packages
RUN apt-get update && \
    apt-get upgrade -y --no-install-recommends && \
    apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid 1000 --create-home --shell /usr/sbin/nologin appuser

WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY app/ ./app/

# Security: remove write permissions on application code
RUN chmod -R a-w /app/app/

# Switch to non-root user
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz')"]

ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
