"""Unit & negative tests for contextual address poisoning and look-alike wallet detection."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from cryptotrace.schemas.security_common import FindingCategory, Severity
from cryptotrace.schemas.security_inputs import AddressContext, TransactionRecord
from cryptotrace.services.security.address_poisoning import AddressPoisoningDetector


@pytest.mark.unit
def test_controlled_address_poisoning_scenario_flagged_with_evidence() -> None:
    detector = AddressPoisoningDetector()
    t0 = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)

    victim = "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    legit = "0x1234567890abcdef1234567890abcdef1234abcd"
    poisoner = "0x123456999999999999999999999999999999abcd"

    txs = [
        TransactionRecord(
            tx_hash="0x" + "1" * 64,
            chain="ethereum",
            block_number=20_000_001,
            timestamp=t0,
            from_address=victim,
            to_address=legit,
            amount=Decimal("2.5"),
            asset_symbol="ETH",
        ),
        TransactionRecord(
            tx_hash="0x" + "2" * 64,
            chain="ethereum",
            block_number=20_000_005,
            timestamp=t0 + timedelta(minutes=2),
            from_address=poisoner,
            to_address=victim,
            amount=Decimal("0"),
            asset_symbol="ETH",
        ),
        TransactionRecord(
            tx_hash="0x" + "3" * 64,
            chain="ethereum",
            block_number=20_000_009,
            timestamp=t0 + timedelta(minutes=5),
            from_address=poisoner,
            to_address=victim,
            amount=Decimal("0.0001"),
            asset_symbol="ETH",
        ),
    ]

    findings = detector.analyze(
        investigation_id="inv-poison-1",
        target_wallet=victim,
        chain="ethereum",
        transactions=txs,
    )
    poison_findings = [
        f for f in findings if f.finding_category == FindingCategory.ADDRESS_POISONING
    ]
    assert len(poison_findings) == 1
    finding = poison_findings[0]
    assert finding.severity in (Severity.HIGH, Severity.CRITICAL)
    assert finding.source_address == legit
    assert finding.suspected_lookalike_address == poisoner
    assert finding.similarity_score is not None and finding.similarity_score >= 0.6
    assert set(finding.supporting_transaction_refs) == {"0x" + "2" * 64, "0x" + "3" * 64}
    assert finding.limitations
    assert finding.recommended_action


@pytest.mark.unit
def test_legitimate_similar_addresses_do_not_trigger_poisoning_accusation() -> None:
    """Negative test: similarity alone without poisoning context must not accuse malice."""
    detector = AddressPoisoningDetector()
    t0 = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)

    victim = "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    established_a = "0x123456000000000000000000000000000000abcd"
    established_b = "0x123456111111111111111111111111111111abcd"

    txs = [
        TransactionRecord(
            tx_hash="0x" + "a" * 64,
            chain="ethereum",
            block_number=20_000_010,
            timestamp=t0,
            from_address=victim,
            to_address=established_a,
            amount=Decimal("1.5"),
            asset_symbol="ETH",
        ),
        TransactionRecord(
            tx_hash="0x" + "b" * 64,
            chain="ethereum",
            block_number=20_000_020,
            timestamp=t0 + timedelta(hours=3),
            from_address=victim,
            to_address=established_b,
            amount=Decimal("3.0"),
            asset_symbol="ETH",
        ),
    ]
    contexts = [
        AddressContext(
            address=established_a,
            chain="ethereum",
            interaction_count=5,
            is_known_counterparty=True,
        ),
        AddressContext(
            address=established_b,
            chain="ethereum",
            interaction_count=4,
            is_known_counterparty=True,
        ),
    ]

    findings = detector.analyze(
        investigation_id="inv-benign-1",
        target_wallet=victim,
        chain="ethereum",
        transactions=txs,
        known_counterparties=contexts,
        report_uncorroborated_lookalikes=True,
    )
    assert not any(f.finding_category == FindingCategory.ADDRESS_POISONING for f in findings)
    assert not any(f.severity in (Severity.HIGH, Severity.CRITICAL) for f in findings)

