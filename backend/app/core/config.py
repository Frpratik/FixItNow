from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/fixitnow"
    POSTGRES_DB: str = "fixitnow"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_PORT: int = 5432

    # JWT & Security
    JWT_SECRET: str = "super-secret-jwt-key-fixitnow-production-grade-random-hex-string-32+chars"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_EXPIRE_DAYS: int = 7

    # Matching Engine Defaults
    MAX_RADIUS_KM: float = 10.0
    FIRST_WAVE_SIZE: int = 5
    FIRST_WAVE_TIMEOUT_SEC: int = 60
    EXPIRY_TIMEOUT_MIN: int = 5

    # Environment
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"
    API_PORT: int = 8000
    FRONTEND_PORT: int = 5173

settings = Settings()
