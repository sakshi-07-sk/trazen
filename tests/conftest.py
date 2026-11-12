"""Pytest configuration and shared fixtures for offline deterministic testing."""

import asyncio
from decimal import Decimal
import secrets
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from cryptotrace.config import Settings, get_settings
from cryptotrace.connectors.fixtures.btc_samples import BTC_SAMPLE_TX_1
from cryptotrace.connectors.fixtures.eth_samples import ETH_SAMPLE_TX_1, ETH_SAMPLE_TX_2
from cryptotrace.connectors.fixtures.mock_provider import BitcoinMockAdapter, EthereumMockAdapter
from cryptotrace.core.auth import issue_hmac_token
from cryptotrace.db.base import Base
from cryptotrace.db.session import get_db
from cryptotrace.main import app
from cryptotrace.normalization.pipeline import NormalizationPipeline
from cryptotrace.schemas.common import BlockchainType
from cryptotrace.schemas.transaction import CanonicalTransaction


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an isolated in-memory SQLite database session for unit and integration testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with engine.begin() as conn:
        import cryptotrace.db.models  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async with session_factory() as session:
        yield session
        await session.rollback()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_client(test_db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide an HTTPX AsyncClient wired to the FastAPI app with the test DB dependency."""
    app.dependency_overrides[get_db] = lambda: test_db_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def btc_mock_adapter() -> BitcoinMockAdapter:
    return BitcoinMockAdapter()


@pytest.fixture
def eth_mock_adapter() -> EthereumMockAdapter:
    return EthereumMockAdapter()


@pytest.fixture
def canonical_btc_tx() -> CanonicalTransaction:
    return NormalizationPipeline.normalize_transaction(
        blockchain=BlockchainType.BITCOIN,
        raw_payload=BTC_SAMPLE_TX_1,
        provider_name="fixture_provider",
    )


@pytest.fixture
def canonical_eth_native_tx() -> CanonicalTransaction:
    return NormalizationPipeline.normalize_transaction(
        blockchain=BlockchainType.ETHEREUM,
        raw_payload=ETH_SAMPLE_TX_1,
        provider_name="fixture_provider",
    )


@pytest.fixture
def canonical_eth_erc20_tx() -> CanonicalTransaction:
    return NormalizationPipeline.normalize_transaction(
        blockchain=BlockchainType.ETHEREUM,
        raw_payload=ETH_SAMPLE_TX_2,
        provider_name="fixture_provider",
    )


@pytest.fixture
def ephemeral_auth_secret() -> str:
    """Generate a per-test ephemeral HMAC auth secret (never hardcoded)."""
    return secrets.token_hex(32)


@pytest.fixture
def ephemeral_ed25519_key_pem() -> str:
    """Generate an ephemeral Ed25519 private key PEM for audit export tests."""
    private_key = Ed25519PrivateKey.generate()
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")


@pytest.fixture
def test_security_settings(
    ephemeral_auth_secret: str,
    ephemeral_ed25519_key_pem: str,
) -> Settings:
    """Isolated Settings instance with ephemeral auth secret & Ed25519 signing key."""
    return Settings(
        APP_ENV="test",
        APP_DEBUG=False,
        AUTH_REQUIRED=True,
        AUTH_SECRET=ephemeral_auth_secret,
        AUTH_ISSUER="cryptotrace-test",
        AUDIT_SIGNING_PRIVATE_KEY_PEM=ephemeral_ed25519_key_pem,
    )


@pytest_asyncio.fixture(scope="function")
async def test_async_session_factory() -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    """Provide an isolated file-less or temp-file SQLite async_sessionmaker for concurrency tests."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        import cryptotrace.db.models  # noqa: F401

        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    try:
        yield factory
    finally:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def security_async_client(
    test_db_session: AsyncSession,
    test_security_settings: Settings,
) -> AsyncGenerator[AsyncClient, None]:
    """HTTPX AsyncClient wired with test DB session, test security settings, and clean rate limiter."""
    app.dependency_overrides[get_db] = lambda: test_db_session
    app.dependency_overrides[get_settings] = lambda: test_security_settings
    if hasattr(app.state, "rate_limiter"):
        app.state.rate_limiter.reset()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    app.dependency_overrides.clear()
    if hasattr(app.state, "rate_limiter"):
        app.state.rate_limiter.reset()


@pytest.fixture
def make_auth_headers(test_security_settings: Settings):
    """Factory fixture producing signed Authorization headers for specified roles and investigations."""

    def _factory(
        *,
        actor_id: str = "investigator-1",
        role: str = "investigator",
        allowed_investigations: list[str] | tuple[str, ...] = ("inv-001",),
        allow_all_investigations: bool = False,
        ttl_seconds: int = 3600,
    ) -> dict[str, str]:
        token = issue_hmac_token(
            actor_id=actor_id,
            role=role,
            allowed_investigations=allowed_investigations,
            allow_all_investigations=allow_all_investigations,
            secret=test_security_settings.AUTH_SECRET,
            issuer=test_security_settings.AUTH_ISSUER,
            ttl_seconds=ttl_seconds,
        )
        return {"Authorization": f"Bearer {token}"}

    return _factory
