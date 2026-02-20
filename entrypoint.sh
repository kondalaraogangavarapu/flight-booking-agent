#!/bin/sh
set -e

exec gunicorn app.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind "${APP_HOST:-0.0.0.0}:${APP_PORT:-8000}" \
    --workers "${WEB_CONCURRENCY:-2}" \
    --timeout 120 \
    --graceful-timeout 30 \
    --access-logfile - \
    --log-level "${LOG_LEVEL:-info}"
