"""Tests for Database Persistence and Integrity."""

from decimal import Decimal
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from cryptotrace.connectors.fixtures.btc_samples import BTC_SAMPLE_TX_1
from cryptotrace.connectors.fixtures.eth_samples import ETH_SAMPLE_TX_2
from cryptotrace.db.repository import (
    GraphRepository,
    InvestigationRepository,
    ProvenanceRepository,
    TransactionRepository,
)
from cryptotrace.normalization.pipeline import NormalizationPipeline
from cryptotrace.schemas.common import BlockchainType
from cryptotrace.schemas.investigation import InvestigationCreate


@pytest.mark.asyncio
async def test_investigation_crud_and_status(test_db_session: AsyncSession):
    repo = InvestigationRepository(test_db_session)
    create_payload = InvestigationCreate(
        title="Heist Operation Track",
        description="Tracing stolen funds from exchange",
        blockchain=BlockchainType.BITCOIN,
        target_address="bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
        max_hops=2,
    )

    inv = await repo.create(create_payload)
    assert inv.id is not None
    assert inv.status == "created"

    # Status update
    updated = await repo.update_status(
        investigation_id=inv.id,
        status="completed",
        total_transactions=5,
        total_nodes=12,
        total_edges=10,
    )
    assert updated is not None
    assert updated.status == "completed"
    assert updated.total_transactions_ingested == 5
    assert updated.total_nodes == 12


@pytest.mark.asyncio
async def test_transaction_persistence_and_deduplication(test_db_session: AsyncSession):
    tx_repo = TransactionRepository(test_db_session)
    prov_repo = ProvenanceRepository(test_db_session)

    canonical = NormalizationPipeline.normalize_transaction(
        blockchain=BlockchainType.BITCOIN,
        raw_payload=BTC_SAMPLE_TX_1,
        provider_name="fixture_provider",
    )

    # Check non-existence
    assert await tx_repo.exists("bitcoin", canonical.tx_hash) is False

    tx_model, prov_model = NormalizationPipeline.to_orm(canonical)
    await tx_repo.save_transaction(tx_model)
    await prov_repo.save_provenance(prov_model)
    await test_db_session.commit()

    # Now should exist
    assert await tx_repo.exists("bitcoin", canonical.tx_hash) is True

    # Lookup
    fetched = await tx_repo.get_by_hash("bitcoin", canonical.tx_hash)
    assert fetched is not None
    assert fetched.tx_hash == canonical.tx_hash
    assert len(fetched.utxos) == 2


@pytest.mark.asyncio
async def test_token_transfer_persistence(test_db_session: AsyncSession):
    tx_repo = TransactionRepository(test_db_session)
    prov_repo = ProvenanceRepository(test_db_session)

    canonical = NormalizationPipeline.normalize_transaction(
        blockchain=BlockchainType.ETHEREUM,
        raw_payload=ETH_SAMPLE_TX_2,
        provider_name="fixture_provider",
    )

    tx_model, prov_model = NormalizationPipeline.to_orm(canonical)
    await tx_repo.save_transaction(tx_model)
    await prov_repo.save_provenance(prov_model)
    await test_db_session.commit()

    fetched = await tx_repo.get_by_hash("ethereum", canonical.tx_hash)
    assert fetched is not None
    assert len(fetched.token_transfers) == 1
    transfer = fetched.token_transfers[0]
    assert transfer.token_symbol == "USDT"
    assert transfer.amount == Decimal("5000.000000")
