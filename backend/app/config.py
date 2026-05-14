from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://aros:aros_pass@localhost:5432/aros_db"
    DATABASE_SYNC_URL: str = "postgresql+psycopg2://aros:aros_pass@localhost:5432/aros_db"
    REDIS_URL: str = "redis://localhost:6379/0"

    ANTHROPIC_API_KEY: str = ""
    GITHUB_TOKEN: str = ""
    GITHUB_USERNAME: str = ""
    VERCEL_TOKEN: str = ""
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    AMAZON_ASSOCIATE_TAG: str = "arostag-20"

    # Security — leave empty to disable API key enforcement
    AROS_API_KEY: str = ""
    # Public URL of this API (used in tracking pixel injection)
    AROS_API_URL: str = "http://localhost:8000"

    # JWT settings
    JWT_SECRET_KEY: str = "aros-super-secret-jwt-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # pydantic-settings v2 requires JSON array format in .env for List fields:
    #   CORS_ORIGINS=["http://localhost:3000","http://localhost:3001"]
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]

    DEBUG: bool = True

    # Demo mode — when True, asset_factory returns realistic mock sites
    # instead of calling the Anthropic API (saves credits for investor demo)
    SIMULATE_AI: bool = True

    # When True, all JWT auth is bypassed — API returns demo user automatically
    DEMO_MODE: bool = True


settings = Settings()
