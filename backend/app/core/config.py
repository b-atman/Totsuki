"""
Application configuration using Pydantic Settings.

This module centralizes all configuration, reading from environment
variables with sensible defaults for development.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Pydantic Settings automatically:
    - Reads from environment variables (case-insensitive)
    - Loads from .env file if present
    - Validates types and provides defaults
    """
    
    # Application metadata
    APP_NAME: str = "Totsuki"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    
    # Database configuration
    # For MVP, we use SQLite. Later, swap to PostgreSQL connection string.
    # Example Postgres: "postgresql+asyncpg://user:pass@localhost:5432/totsuki"
    DATABASE_URL: str = "sqlite+aiosqlite:///./totsuki.db"
    
    # Database pool settings (used when switching to PostgreSQL)
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    
    # API settings
    API_V1_PREFIX: str = "/api/v1"
    
    # CORS settings (for React frontend)
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    model_config = SettingsConfigDict(
        # Load from .env file in the backend directory
        env_file=".env",
        # .env file is optional (won't error if missing)
        env_file_encoding="utf-8",
        # Allow extra fields (future-proofing)
        extra="ignore",
        # Case-insensitive environment variable names
        case_sensitive=False,
    )


# Create a singleton instance
# This is imported throughout the app as: from app.core.config import settings
settings = Settings()
