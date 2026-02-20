import os


class Settings:
    """Application settings loaded from environment variables."""

    APP_NAME: str = "Flight Booking Agent"
    APP_VERSION: str = "0.1.0"
    HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("APP_PORT", "8000"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")
    # Secret key must be provided via environment variable in production
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")


settings = Settings()
