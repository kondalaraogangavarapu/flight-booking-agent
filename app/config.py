import os
import secrets
import warnings
from pathlib import Path


def _read_version() -> str:
    """Read version from the VERSION file (single source of truth)."""
    version_file = Path(__file__).resolve().parent.parent / "VERSION"
    try:
        return version_file.read_text().strip()
    except FileNotFoundError:
        return "0.0.0"


class Settings:
    """Application settings loaded from environment variables."""

    APP_NAME: str = "Flight Booking Agent"
    APP_VERSION: str = _read_version()
    HOST: str = os.getenv("APP_HOST", "127.0.0.1")
    PORT: int = int(os.getenv("APP_PORT", "8000"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")
    HEALTH_CHECK_TIMEOUT: int = int(os.getenv("HEALTH_CHECK_TIMEOUT", "5"))

    # Anthropic API key (optional – enables LLM-powered agent)
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    def __init__(self) -> None:
        secret = os.getenv("SECRET_KEY")
        if not secret:
            secret = secrets.token_urlsafe(32)
            warnings.warn(
                "SECRET_KEY is not set – using an auto-generated ephemeral key. "
                "Set the SECRET_KEY environment variable for production.",
                stacklevel=2,
            )
        self.SECRET_KEY: str = secret


settings = Settings()
