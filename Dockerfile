# Build stage — install dependencies separately for layer caching
FROM python:3.12-slim AS builder

WORKDIR /app

# Copy only requirements first to cache dependency installation
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt \
    && pip install --no-cache-dir pip-audit \
    && pip-audit -r requirements.txt || echo "WARN: pip-audit found vulnerabilities (see above)"

# Runtime stage
FROM python:3.12-slim

WORKDIR /app

# Create non-root user
RUN groupadd --system appuser && useradd --system --gid appuser appuser

# Copy installed dependencies from builder (changes least often)
COPY --from=builder /install /usr/local

# Copy version file (changes on release)
COPY VERSION .

# Copy application code last (changes most often)
COPY app/ ./app/

# Switch to non-root user
USER appuser

ENV HOST=0.0.0.0
ENV PORT=8000
ENV LOG_LEVEL=info

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"]

CMD ["gunicorn", "app.main:app", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--log-level", "info"]
