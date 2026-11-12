"""Pytest configuration and shared fixtures for offline deterministic testing."""

import asyncio
from decimal import Decimal
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from cryptotrace.connectors.fixtures.btc_samples import BTC_SAMPLE_TX_1
from cryptotrace.connectors.fixtures.eth_samples import ETH_SAMPLE_TX_1, ETH_SAMPLE_TX_2
from cryptotrace.connectors.fixtures.mock_provider import BitcoinMockAdapter, EthereumMockAdapter
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
