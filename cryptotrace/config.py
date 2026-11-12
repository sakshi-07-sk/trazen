"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """System configuration parameters."""

    # Application
    APP_NAME: str = "CryptoTrace-Engine"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./cryptotrace.db"
    DATABASE_SYNC_URL: str = "sqlite:///./cryptotrace.db"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_ECHO: bool = False

    # Blockchain Providers & Credentials
    ETHERSCAN_API_KEY: Optional[str] = None
    ALCHEMY_API_KEY: Optional[str] = None
    INFURA_PROJECT_ID: Optional[str] = None
    BLOCKSTREAM_API_URL: str = "https://blockstream.info/api"
    ETHERSCAN_API_URL: str = "https://api.etherscan.io/api"

    # Connector Resilience
    PROVIDER_TIMEOUT_SECONDS: float = 10.0
    PROVIDER_MAX_RETRIES: int = 3
    PROVIDER_BACKOFF_FACTOR: float = 1.5
    PROVIDER_RATE_LIMIT_RPS: float = 5.0

    # Demo Fixture Mode
    DEMO_FIXTURE_MODE: bool = True

    # Cache Settings
    CACHE_TTL_SECONDS: int = 300
    CACHE_MAX_ITEMS: int = 5000

    # Graph Traversal Parameters
    MAX_GRAPH_HOPS: int = 3
    DEFAULT_GRAPH_HOPS: int = 2
    MAX_GRAPH_NODES: int = 2500

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """Retrieve cached application settings instance."""
    return Settings()
