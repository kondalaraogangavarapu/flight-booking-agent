# ---- Build stage ----
FROM python:3.12-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- Runtime stage ----
FROM python:3.12-slim

LABEL org.opencontainers.image.title="flight-booking-agent" \
      org.opencontainers.image.version="0.4.1" \
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

# Copy application code, entrypoint, and VERSION file
COPY app/ ./app/
COPY VERSION ./
COPY entrypoint.sh ./

# Security: remove write permissions on application code, make entrypoint executable
RUN chmod -R a-w /app/app/ /app/VERSION && \
    chmod +x /app/entrypoint.sh

# Switch to non-root user
USER appuser

EXPOSE 8000

# Configurable env vars with secure defaults
ENV APP_HOST="0.0.0.0" \
    APP_PORT="8000" \
    LOG_LEVEL="info" \
    WEB_CONCURRENCY="2" \
    HEALTH_CHECK_TIMEOUT="5"

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD ["python", "-c", "import os, urllib.request; host = os.environ.get('APP_HOST', '0.0.0.0'); host = '127.0.0.1' if host == '0.0.0.0' else host; urllib.request.urlopen('http://{}:{}/healthz'.format(host, os.environ.get('APP_PORT', '8000')), timeout=int(os.environ.get('HEALTH_CHECK_TIMEOUT', '5')))"]

ENTRYPOINT ["/app/entrypoint.sh"]
