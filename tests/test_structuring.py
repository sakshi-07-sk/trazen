"""Unit tests for structuring, chain-specific thresholds, dormancy, and negative guards."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from forensics.datasets.fixtures import (
    make_dormant_activation_case,
    make_false_positive_payroll_case,
    make_structuring_case,
)
from forensics.engine import ForensicEngine
from forensics.schemas.input import InvestigationCase, NormalizedTransaction
from tests.forensics_support import config, engine  # noqa: F401


BASE = datetime(2026, 2, 1, 12, 0, 0, tzinfo=timezone.utc)


def test_structuring_split_and_passthrough_detected(engine: ForensicEngine) -> None:
    bundle = engine.analyze_case(make_structuring_case())
    rules = {f.rule_id for f in bundle.findings_response.findings}
    assert "STRUCTURING-SPLIT-01" in rules
    assert "STRUCTURING-PASSTHROUGH-01" in rules


def test_bitcoin_chain_specific_structuring_thresholds(engine: ForensicEngine) -> None:
    """0.45 BTC splits avoid 0.50 BTC BTC-specific threshold (whereas ETH threshold is 5.0)."""
    txs = [
        NormalizedTransaction(
            tx_id=f"BTC-STR-{i}",
            chain="bitcoin",
            timestamp=BASE + timedelta(minutes=i * 5),
            from_address="bc1qSplitter",
            to_address=f"bc1qOut{i}",
            value=0.45,
        )
        for i in range(1, 6)
    ]
    case = InvestigationCase(
        investigation_id="TEST-BTC-STRUCT",
        chain="bitcoin",
        seed_addresses=["bc1qSplitter"],
        transactions=txs,
    )
    bundle = engine.analyze_case(case)
    rules = {f.rule_id for f in bundle.findings_response.findings}
    assert "STRUCTURING-SPLIT-01" in rules


def test_payroll_negative_guard_does_not_trigger_structuring(engine: ForensicEngine) -> None:
    bundle = engine.analyze_case(make_false_positive_payroll_case())
    rules = {f.rule_id for f in bundle.findings_response.findings}
    assert "STRUCTURING-SPLIT-01" not in rules
    assert "FAN-OUT-01" not in rules


def test_dormant_reactivation_detected_and_short_gap_ignored(engine: ForensicEngine) -> None:
    bundle = engine.analyze_case(make_dormant_activation_case())
    rules = {f.rule_id for f in bundle.findings_response.findings}
    assert "DORMANT-REACTIVATION-01" in rules

    # Negative: 5-day gap (< 30d threshold) must NOT trigger dormancy reactivation
    short_gap_case = InvestigationCase(
        investigation_id="TEST-SHORT-GAP",
        chain="ethereum",
        transactions=[
            NormalizedTransaction(
                tx_id="S1", chain="ethereum", timestamp=BASE, from_address="0xSrc", to_address="0xW", value=5.0
            ),
            NormalizedTransaction(
                tx_id="S2",
                chain="ethereum",
                timestamp=BASE + timedelta(days=5),
                from_address="0xW",
                to_address="0xD1",
                value=2.0,
            ),
            NormalizedTransaction(
                tx_id="S3",
                chain="ethereum",
                timestamp=BASE + timedelta(days=5, minutes=10),
                from_address="0xW",
                to_address="0xD2",
                value=2.0,
            ),
        ],
    )
    neg_bundle = engine.analyze_case(short_gap_case)
    assert all(f.rule_id != "DORMANT-REACTIVATION-01" for f in neg_bundle.findings_response.findings)
