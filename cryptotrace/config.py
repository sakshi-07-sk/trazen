"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import List, Optional
from pydantic import AliasChoices, Field, field_validator
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

    # Role 3 Security, Auth, Hardening & Audit Settings
    AUTH_REQUIRED: bool = Field(
        default=True,
        validation_alias=AliasChoices("AUTH_REQUIRED", "CRYPTOTRACE_AUTH_REQUIRED"),
    )
    ENFORCE_AUTH_ON_CORE_ROUTES: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "ENFORCE_AUTH_ON_CORE_ROUTES", "CRYPTOTRACE_ENFORCE_AUTH_ON_CORE_ROUTES"
        ),
    )
    AUTH_SECRET: str = Field(
        default="",
        validation_alias=AliasChoices("AUTH_SECRET", "CRYPTOTRACE_AUTH_SECRET"),
    )
    AUTH_ISSUER: str = Field(
        default="cryptotrace",
        validation_alias=AliasChoices("AUTH_ISSUER", "CRYPTOTRACE_AUTH_ISSUER"),
    )
    AUTH_TOKEN_TTL_SECONDS: int = Field(
        default=3600,
        validation_alias=AliasChoices("AUTH_TOKEN_TTL_SECONDS", "CRYPTOTRACE_AUTH_TOKEN_TTL_SECONDS"),
    )
    CORS_ALLOWED_ORIGINS: List[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"],
        validation_alias=AliasChoices("CORS_ALLOWED_ORIGINS", "CRYPTOTRACE_CORS_ALLOWED_ORIGINS"),
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(
        default=False,
        validation_alias=AliasChoices("CORS_ALLOW_CREDENTIALS", "CRYPTOTRACE_CORS_ALLOW_CREDENTIALS"),
    )
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(
        default=120,
        validation_alias=AliasChoices(
            "RATE_LIMIT_REQUESTS_PER_MINUTE", "CRYPTOTRACE_RATE_LIMIT_REQUESTS_PER_MINUTE"
        ),
    )
    MAX_REQUEST_BYTES: int = Field(
        default=1_048_576,
        validation_alias=AliasChoices("MAX_REQUEST_BYTES", "CRYPTOTRACE_MAX_REQUEST_BYTES"),
    )
    AUDIT_SIGNING_PRIVATE_KEY_PEM: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices(
            "AUDIT_SIGNING_PRIVATE_KEY_PEM", "CRYPTOTRACE_AUDIT_SIGNING_PRIVATE_KEY_PEM"
        ),
    )
    REQUIRE_INDEPENDENT_PROVIDER_VERIFICATION: bool = Field(
        default=False,
        validation_alias=AliasChoices(
            "REQUIRE_INDEPENDENT_PROVIDER_VERIFICATION",
            "CRYPTOTRACE_REQUIRE_INDEPENDENT_PROVIDER_VERIFICATION",
        ),
    )

    @field_validator("CORS_ALLOWED_ORIGINS", mode="before")
    @classmethod
    def _parse_cors_origins(cls, value: object) -> List[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return []

    @field_validator("CORS_ALLOWED_ORIGINS")
    @classmethod
    def _reject_wildcard_origins(cls, origins: List[str]) -> List[str]:
        if "*" in origins:
            raise ValueError("Wildcard '*' is forbidden in CORS_ALLOWED_ORIGINS.")
        return origins

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """Retrieve cached application settings instance."""
    return Settings()
