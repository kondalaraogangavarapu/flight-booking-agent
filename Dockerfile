# Build stage
FROM python:3.12-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Runtime stage
FROM python:3.12-slim

WORKDIR /app

# Create non-root user
RUN groupadd --system appuser && useradd --system --gid appuser appuser

# Copy installed dependencies from builder
COPY --from=builder /install /usr/local

COPY VERSION .
COPY app/ ./app/

# Switch to non-root user
USER appuser

ENV HOST=0.0.0.0
ENV PORT=8000
ENV LOG_LEVEL=info

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]

CMD ["python", "-m", "app.main"]
