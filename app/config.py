import os
import secrets
import warnings


class Settings:
    """Application settings loaded from environment variables."""

    APP_NAME: str = "Flight Booking Agent"
    APP_VERSION: str = "0.2.0"
    HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("APP_PORT", "8000"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")

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
