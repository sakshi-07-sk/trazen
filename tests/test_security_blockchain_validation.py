"""Unit tests for adversarial blockchain-data validation and multi-provider conflict checks."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from cryptotrace.connectors.fixtures.btc_samples import BTC_SAMPLE_TX_1
from cryptotrace.normalization.bitcoin_normalizer import BitcoinNormalizer
from cryptotrace.schemas.security_common import IndependentVerificationStatus, ValidationStatus
from cryptotrace.schemas.security_inputs import ProviderObservation, TransactionRecord, TransferType
from cryptotrace.services.security.adapters import canonical_tx_to_security_records
from cryptotrace.services.security.blockchain_validator import BlockchainDataValidator


def _valid_eth_tx() -> TransactionRecord:
    return TransactionRecord(
        tx_hash="0x" + "a" * 64,
        chain="ethereum",
        network="mainnet",
        block_number=20_500_000,
        block_hash="0x" + "b" * 64,
        timestamp=datetime(2026, 10, 1, 12, 0, tzinfo=UTC),
        confirmations=24,
        status="confirmed",
        from_address="0x1111111111111111111111111111111111111111",
        to_address="0x2222222222222222222222222222222222222222",
        amount=Decimal("1.5"),
        raw_amount="1500000000000000000",
        asset_symbol="ETH",
        decimals=18,
        transfer_type=TransferType.NATIVE,
        source_provider="provider_alpha",
        provenance_id="prov-alpha-1",
    )


@pytest.mark.unit
def test_valid_transaction_and_independent_provider_agreement() -> None:
    validator = BlockchainDataValidator()
    tx = _valid_eth_tx()
    obs = [
        ProviderObservation(
            provider_name="provider_beta",
            upstream_source="archive_geth_node",
            transaction={
                "chain": "ethereum",
                "tx_hash": tx.tx_hash,
                "from_address": tx.from_address,
                "to_address": tx.to_address,
                "amount": "1.5",
                "block_number": 20_500_000,
                "status": "confirmed",
            },
        )
    ]
    report = validator.validate_transaction(
        "inv-val-1", tx, provider_observations=obs, require_independent=True
    )
    assert report.validation_status == ValidationStatus.VALID
    assert report.independent_verification_status == IndependentVerificationStatus.VERIFIED_AGREE
    assert report.findings == []


@pytest.mark.unit
def test_detects_invalid_hash_wrong_chain_and_incomplete_records() -> None:
    validator = BlockchainDataValidator()

    bad_hash_tx = _valid_eth_tx().model_copy(update={"tx_hash": "not-a-hash"})
    r1 = validator.validate_transaction("inv-val-2", bad_hash_tx)
    assert r1.validation_status == ValidationStatus.INVALID

    wrong_chain_tx = _valid_eth_tx().model_copy(update={"chain": "marschain"})
    r2 = validator.validate_transaction("inv-val-2", wrong_chain_tx)
    assert r2.validation_status == ValidationStatus.INVALID

    future_ts_tx = _valid_eth_tx().model_copy(
        update={"timestamp": datetime.now(UTC) + timedelta(days=5)}
    )
    r3 = validator.validate_transaction("inv-val-2", future_ts_tx)
    assert r3.validation_status == ValidationStatus.INVALID

    incomplete_tx = TransactionRecord(chain="ethereum", tx_hash="0x" + "c" * 64)
    r4 = validator.validate_transaction("inv-val-2", incomplete_tx)
    assert r4.validation_status == ValidationStatus.INCOMPLETE


@pytest.mark.unit
def test_conflicting_provider_responses_never_silently_accepted() -> None:
    validator = BlockchainDataValidator()
    tx = _valid_eth_tx()
    conflicting_obs = [
        ProviderObservation(
            provider_name="provider_beta",
            upstream_source="independent_node_b",
            transaction={
                "chain": "ethereum",
                "tx_hash": tx.tx_hash,
                "from_address": tx.from_address,
                "to_address": "0x9999999999999999999999999999999999999999",
                "amount": "99.0",
                "block_number": 20_500_000,
                "status": "confirmed",
            },
        )
    ]
    report = validator.validate_transaction(
        "inv-val-conflict", tx, provider_observations=conflicting_obs
    )
    assert report.validation_status == ValidationStatus.CONFLICTING
    assert report.independent_verification_status == IndependentVerificationStatus.VERIFIED_CONFLICT
    assert len(report.conflicts) == 2
    assert len(report.findings) == 1


@pytest.mark.unit
def test_shared_upstream_providers_are_not_treated_as_independent() -> None:
    validator = BlockchainDataValidator()
    tx = _valid_eth_tx().model_copy(update={"source_provider": "etherscan_wrapper"})
    shared_obs = [
        ProviderObservation(
            provider_name="aggregator_mirror",
            upstream_source="etherscan_wrapper",
            transaction={
                "chain": "ethereum",
                "tx_hash": tx.tx_hash,
                "from_address": tx.from_address,
                "to_address": tx.to_address,
                "amount": "1.5",
                "block_number": 20_500_000,
                "status": "confirmed",
            },
        )
    ]
    report = validator.validate_transaction(
        "inv-val-shared",
        tx,
        provider_observations=shared_obs,
        require_independent=True,
    )
    assert report.independent_verification_status == IndependentVerificationStatus.NOT_INDEPENDENT
    assert report.validation_status == ValidationStatus.UNVERIFIED


@pytest.mark.unit
def test_canonical_bitcoin_utxo_records_validate_cleanly() -> None:
    """Legitimate Role 1 Bitcoin UTXO multi-input/output records must validate as VALID."""
    canonical = BitcoinNormalizer.normalize(BTC_SAMPLE_TX_1, provider_name="fixture_provider")
    records = canonical_tx_to_security_records(canonical)
    validator = BlockchainDataValidator()
    reports = validator.validate_batch("inv-btc-val", records)
    assert len(reports) == 4
    assert all(r.validation_status == ValidationStatus.VALID for r in reports)

