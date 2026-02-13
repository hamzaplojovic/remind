"""Configuration for Remind backend."""

import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env from monorepo root (works regardless of CWD)
_ENV_FILE = Path(__file__).resolve().parents[4] / ".env"


class Settings(BaseSettings):
    """Application settings."""

    # Database (PostgreSQL required)
    database_url: str = os.getenv("DATABASE_URL", "")

    # API
    api_title: str = "Remind Backend"
    api_version: str = "1.0.0"
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

    # CORS
    cors_origins: list[str] = [
        "https://remind.hamzaplojovic.blog",
        "https://remind-production-0871.up.railway.app",
        "http://localhost:3000",
        "http://localhost:8000",
    ]

    # Groq
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    ai_model: str = os.getenv("AI_MODEL", "gpt-oss-20b")

    # Polar Payment
    polar_api_key: str = os.getenv("POLAR_API_KEY", "")
    polar_webhook_secret: str = os.getenv("POLAR_WEBHOOK_SECRET", "")
    polar_product_free: str = os.getenv("POLAR_PRODUCT_FREE", "")
    polar_product_indie: str = os.getenv("POLAR_PRODUCT_INDIE", "")
    polar_product_pro: str = os.getenv("POLAR_PRODUCT_PRO", "")
    polar_product_team: str = os.getenv("POLAR_PRODUCT_TEAM", "")

    # Email (SMTP)
    smtp_host: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_user: str = os.getenv("SMTP_USER", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    smtp_from_email: str = os.getenv("SMTP_FROM_EMAIL", "")

    # Rate limiting
    rate_limit_requests: int = int(os.getenv("RATE_LIMIT_REQUESTS", "10"))
    rate_limit_window_seconds: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )


_settings: Settings | None = None


def get_settings() -> Settings:
    """Get application settings."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
