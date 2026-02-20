#!/usr/bin/env python
"""Lightweight health check script for Docker HEALTHCHECK."""
import os
import sys
import urllib.request

host = os.environ.get("APP_HOST", "0.0.0.0")
if host == "0.0.0.0":
    host = "127.0.0.1"
port = os.environ.get("APP_PORT", "8000")
timeout = int(os.environ.get("HEALTH_CHECK_TIMEOUT", "5"))

try:
    urllib.request.urlopen(f"http://{host}:{port}/healthz", timeout=timeout)
except Exception:
    sys.exit(1)
