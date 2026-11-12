"""Unit tests for peel-chain detection and negative cases."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from forensics.datasets.fixtures import make_peel_chain_btc_case, make_peel_chain_eth_case
from forensics.engine import ForensicEngine
from forensics.schemas.input import EntityLabel, InvestigationCase, NormalizedTransaction
from tests.forensics_support import config, engine  # noqa: F401


BASE = datetime(2026, 2, 1, 12, 0, 0, tzinfo=timezone.utc)


def test_eth_peel_chain_detected_with_path_and_evidence(engine: ForensicEngine) -> None:
    case = make_peel_chain_eth_case()
    bundle = engine.analyze_case(case)
    peel_findings = [f for f in bundle.findings_response.findings if f.rule_id == "PEEL-CHAIN-01"]
    assert len(peel_findings) >= 1
    f = peel_findings[0]
    assert f.metadata["hop_count"] >= 4
    assert "0xSeed" in f.metadata["detected_path"]
    assert "0xFinalSink" in f.metadata["detected_path"]
    assert len(f.evidence_refs) == f.metadata["hop_count"]
    assert len(f.limitations) >= 1


def test_btc_utxo_peel_chain_detected(engine: ForensicEngine) -> None:
    case = make_peel_chain_btc_case()
    bundle = engine.analyze_case(case)
    peel_findings = [f for f in bundle.findings_response.findings if f.rule_id == "PEEL-CHAIN-01"]
    assert len(peel_findings) >= 1
    assert peel_findings[0].metadata["hop_count"] >= 3


def test_short_two_hop_forwarding_does_not_trigger_peel_chain(engine: ForensicEngine) -> None:
    case = InvestigationCase(
        investigation_id="TEST-PEEL-NEG-SHORT",
        chain="ethereum",
        seed_addresses=["0xA"],
        transactions=[
            NormalizedTransaction(
                tx_id="T1", chain="ethereum", timestamp=BASE, from_address="0xA", to_address="0xB", value=10.0
            ),
            NormalizedTransaction(
                tx_id="T2",
                chain="ethereum",
                timestamp=BASE + timedelta(minutes=10),
                from_address="0xB",
                to_address="0xC",
                value=9.0,
            ),
        ],
    )
    bundle = engine.analyze_case(case)
    assert all(f.rule_id != "PEEL-CHAIN-01" for f in bundle.findings_response.findings)


def test_labelled_exchange_intermediaries_do_not_trigger_peel_chain(engine: ForensicEngine) -> None:
    case = InvestigationCase(
        investigation_id="TEST-PEEL-NEG-EX",
        chain="ethereum",
        seed_addresses=["0xA"],
        transactions=[
            NormalizedTransaction(
                tx_id="T1", chain="ethereum", timestamp=BASE, from_address="0xA", to_address="0xEx1", value=10.0
            ),
            NormalizedTransaction(
                tx_id="T2",
                chain="ethereum",
                timestamp=BASE + timedelta(minutes=5),
                from_address="0xEx1",
                to_address="0xEx2",
                value=9.0,
            ),
            NormalizedTransaction(
                tx_id="T3",
                chain="ethereum",
                timestamp=BASE + timedelta(minutes=10),
                from_address="0xEx2",
                to_address="0xUser",
                value=8.1,
            ),
        ],
        labels=[
            EntityLabel(address="0xEx1", label="CEX 1", category="exchange", verified=True),
            EntityLabel(address="0xEx2", label="CEX 2", category="exchange", verified=True),
        ],
    )
    bundle = engine.analyze_case(case)
    assert all(f.rule_id != "PEEL-CHAIN-01" for f in bundle.findings_response.findings)
