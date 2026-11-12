"""Unit tests for address/wallet clustering and CoinJoin false-positive safeguards."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from forensics.datasets.fixtures import make_collaborative_coinjoin_case
from forensics.engine import ForensicEngine
from forensics.schemas.input import EntityLabel, InvestigationCase, NormalizedTransaction, UTXOEntry
from tests.forensics_support import config, engine  # noqa: F401


BASE = datetime(2026, 2, 1, 12, 0, 0, tzinfo=timezone.utc)


def test_cioh_links_non_collaborative_utxo_inputs_with_reasons(engine: ForensicEngine) -> None:
    case = InvestigationCase(
        investigation_id="TEST-CIOH-POS",
        chain="bitcoin",
        seed_addresses=["bc1qIn1"],
        transactions=[
            NormalizedTransaction(
                tx_id="BTC-CO-1",
                chain="bitcoin",
                timestamp=BASE,
                asset="BTC",
                inputs=[
                    UTXOEntry(address="bc1qIn1", value=0.8),
                    UTXOEntry(address="bc1qIn2", value=0.4),
                ],
                outputs=[
                    UTXOEntry(address="bc1qPayee", value=1.1),
                    UTXOEntry(address="bc1qIn1", value=0.09),  # reused change
                ],
            )
        ],
    )
    bundle = engine.analyze_case(case)
    clusters = bundle.findings_response.clusters
    assert len(clusters) == 1
    assert set(clusters[0].addresses) == {"bc1qIn1", "bc1qIn2"}
    assert clusters[0].confidence < 1.0
    assert any(r.heuristic == "common_input_ownership" for r in clusters[0].reasons)
    assert any(r.relationship_status == "inferred" for r in clusters[0].reasons)
    rule_ids = {f.rule_id for f in bundle.findings_response.findings}
    assert "CLUSTER-HEURISTIC-01" in rule_ids
    assert "CLUSTER-ADDR-REUSE-01" in rule_ids


def test_coinjoin_suppresses_cioh_clustering(engine: ForensicEngine) -> None:
    case = make_collaborative_coinjoin_case()
    bundle = engine.analyze_case(case)
    assert bundle.findings_response.clusters == []
    rule_ids = {f.rule_id for f in bundle.findings_response.findings}
    assert "CLUSTER-COINJOIN-GUARD-01" in rule_ids
    assert "CLUSTER-HEURISTIC-01" not in rule_ids


def test_payjoin_hint_suppresses_cioh(engine: ForensicEngine) -> None:
    case = InvestigationCase(
        investigation_id="TEST-PAYJOIN",
        chain="bitcoin",
        transactions=[
            NormalizedTransaction(
                tx_id="BTC-PJ-1",
                chain="bitcoin",
                timestamp=BASE,
                asset="BTC",
                is_collaborative_hint=True,
                inputs=[
                    UTXOEntry(address="bc1qSender", value=0.5),
                    UTXOEntry(address="bc1qReceiverContrib", value=0.2),
                ],
                outputs=[
                    UTXOEntry(address="bc1qMerchant", value=0.65),
                    UTXOEntry(address="bc1qSenderChange", value=0.049),
                ],
            )
        ],
    )
    bundle = engine.analyze_case(case)
    assert bundle.findings_response.clusters == []
    assert any(
        f.rule_id == "CLUSTER-COINJOIN-GUARD-01" for f in bundle.findings_response.findings
    )


def test_distinct_verified_services_are_never_clustered_together(engine: ForensicEngine) -> None:
    case = InvestigationCase(
        investigation_id="TEST-NO-MERGE-SVC",
        chain="bitcoin",
        transactions=[
            NormalizedTransaction(
                tx_id="BTC-SVC-1",
                chain="bitcoin",
                timestamp=BASE,
                asset="BTC",
                inputs=[
                    UTXOEntry(address="bc1qExA", value=1.0),
                    UTXOEntry(address="bc1qExB", value=1.2),
                ],
                outputs=[UTXOEntry(address="bc1qDest", value=2.19)],
            )
        ],
        labels=[
            EntityLabel(address="bc1qExA", label="Exchange A", category="exchange", verified=True),
            EntityLabel(address="bc1qExB", label="Exchange B", category="exchange", verified=True),
        ],
    )
    bundle = engine.analyze_case(case)
    assert bundle.findings_response.clusters == []
