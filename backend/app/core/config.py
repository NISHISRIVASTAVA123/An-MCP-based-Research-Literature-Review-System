"""Application Configuration Module.

Loads configuration from environment variables or .env file with sensible defaults
for academic research environments.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with type-checked validation."""

    APP_NAME: str = "MCP Academic Literature Review & Research Gap Assessment"
    APP_VERSION: str = "1.0.0-phase1"
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    # Persistence
    DATABASE_URL: str = "sqlite:///./literature_review.db"

    # Academic Provider Settings
    POLITE_EMAIL: str = "academic.researcher@example.edu"
    SEMANTIC_SCHOLAR_API_KEY: str = ""
    PROVIDER_TIMEOUT_SECONDS: float = 15.0
    MAX_RETRIES: int = 2
    DEFAULT_MAX_PAPERS: int = 25

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

