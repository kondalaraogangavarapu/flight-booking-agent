# ---- Build stage ----
FROM python:3.12-slim AS builder

WORKDIR /build

# Install dependencies into a virtual environment at the same path used at runtime
RUN python -m venv /app/venv
COPY requirements.txt .
RUN /app/venv/bin/pip install --no-cache-dir -r requirements.txt

# ---- Runtime stage ----
FROM python:3.12-slim

# Version is read from the VERSION file at runtime by the app;
# pass --build-arg APP_VERSION=x.y.z to set the image label, or omit for "dev".
ARG APP_VERSION=dev

LABEL org.opencontainers.image.title="flight-booking-agent" \
      org.opencontainers.image.version="${APP_VERSION}" \
      org.opencontainers.image.description="Flight booking agent REST API with conversational AI" \
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

# Copy virtual environment from builder with correct ownership
COPY --from=builder --chown=appuser:appuser /app/venv /app/venv

# Copy application code, entrypoint, and VERSION file
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser VERSION ./
COPY --chown=appuser:appuser entrypoint.sh ./

# Security: remove write permissions on application code, make entrypoint executable
RUN chmod -R a-w /app/app/ /app/VERSION && \
    chmod +x /app/entrypoint.sh

# Switch to non-root user
USER appuser

# Put venv on PATH so gunicorn/uvicorn are found
ENV PATH="/app/venv/bin:$PATH" \
    VIRTUAL_ENV="/app/venv"

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
