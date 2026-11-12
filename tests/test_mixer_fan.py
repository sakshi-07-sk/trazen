"""Unit tests for fan-in, fan-out, and mixer pattern detectors + negative tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from forensics.datasets.fixtures import (
    make_false_positive_exchange_hot_wallet_case,
    make_fan_in_case,
    make_fan_out_case,
    make_mixer_pattern_case,
)
from forensics.engine import ForensicEngine
from forensics.schemas.input import InvestigationCase, NormalizedTransaction
from tests.forensics_support import config, engine  # noqa: F401


BASE = datetime(2026, 2, 1, 12, 0, 0, tzinfo=timezone.utc)


def test_fan_in_triggers_only_fan_in(engine: ForensicEngine) -> None:
    bundle = engine.analyze_case(make_fan_in_case())
    rules = {f.rule_id for f in bundle.findings_response.findings}
    assert "FAN-IN-01" in rules
    assert "FAN-OUT-01" not in rules
    assert "MIXER-PATTERN-01" not in rules


def test_fan_out_triggers_only_fan_out(engine: ForensicEngine) -> None:
    bundle = engine.analyze_case(make_fan_out_case())
    rules = {f.rule_id for f in bundle.findings_response.findings}
    assert "FAN-OUT-01" in rules
    assert "FAN-IN-01" not in rules
    assert "MIXER-PATTERN-01" not in rules


def test_mixer_equal_denomination_pattern_detected(engine: ForensicEngine) -> None:
    bundle = engine.analyze_case(make_mixer_pattern_case())
    rules = {f.rule_id for f in bundle.findings_response.findings}
    assert "MIXER-PATTERN-01" in rules


def test_high_volume_varied_unlabelled_hub_not_classified_as_mixer(engine: ForensicEngine) -> None:
    """Negative test: many inbound & outbound txs with varied amounts & slow gaps != mixer."""
    txs = []
    for i in range(1, 8):
        txs.append(
            NormalizedTransaction(
                tx_id=f"IN-{i}",
                chain="ethereum",
                timestamp=BASE + timedelta(hours=i * 5),
                from_address=f"0xClient{i}",
                to_address="0xBusyHub",
                value=0.45 * i + 0.13,
            )
        )
        txs.append(
            NormalizedTransaction(
                tx_id=f"OUT-{i}",
                chain="ethereum",
                timestamp=BASE + timedelta(hours=i * 5 + 30),
                from_address="0xBusyHub",
                to_address=f"0xVendor{i}",
                value=0.71 * i + 0.09,
            )
        )
    case = InvestigationCase(
        investigation_id="TEST-BUSY-NONMIXER",
        chain="ethereum",
        transactions=txs,
    )
    bundle = engine.analyze_case(case)
    rules = {f.rule_id for f in bundle.findings_response.findings}
    assert "MIXER-PATTERN-01" not in rules


def test_exchange_hot_wallet_negative_guard(engine: ForensicEngine) -> None:
    bundle = engine.analyze_case(make_false_positive_exchange_hot_wallet_case())
    rules = {f.rule_id for f in bundle.findings_response.findings}
    assert "MIXER-PATTERN-01" not in rules
    assert "FAN-IN-01" not in rules
    assert "FAN-OUT-01" not in rules
