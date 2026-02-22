"""Application configuration via environment variables."""

import os

HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", "8000"))
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")
APP_VERSION: str = open(os.path.join(os.path.dirname(__file__), "..", "VERSION")).read().strip()
