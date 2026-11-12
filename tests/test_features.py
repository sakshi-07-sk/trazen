"""Unit tests for wallet behavioural feature extraction and graph feature caching."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from forensics.features.extractor import extract_all_wallet_features, extract_wallet_features
from forensics.graph.index import InvestigationGraphIndex
from forensics.schemas.input import (
    EntityLabel,
    GraphEdge,
    GraphNode,
    InvestigationCase,
    NormalizedTransaction,
    UTXOEntry,
)


BASE = datetime(2026, 2, 1, 12, 0, 0, tzinfo=timezone.utc)


def test_ethereum_account_features_and_caching() -> None:
    case = InvestigationCase(
        investigation_id="TEST-FEAT-ETH",
        chain="ethereum",
        seed_addresses=["0xA"],
        transactions=[
            NormalizedTransaction(
                tx_id="T1",
                chain="ethereum",
                timestamp=BASE,
                from_address="0xSrc",
                to_address="0xA",
                value=10.0,
            ),
            NormalizedTransaction(
                tx_id="T2",
                chain="ethereum",
                timestamp=BASE + timedelta(days=5),
                from_address="0xA",
                to_address="0xBridge",
                value=4.0,
                is_contract_call=True,
                is_bridge_interaction=True,
            ),
            NormalizedTransaction(
                tx_id="T3",
                chain="ethereum",
                timestamp=BASE + timedelta(days=5, hours=1),
                from_address="0xA",
                to_address="0xTokenDest",
                value=2.0,
                is_token_transfer=True,
            ),
        ],
        labels=[
            EntityLabel(address="0xBridge", label="CrossChainBridge", category="bridge", verified=True)
        ],
    )
    index = InvestigationGraphIndex(case)
    feat_a = extract_wallet_features(index, "0xA")
    # Cached identity check
    assert extract_wallet_features(index, "0xA") is feat_a

    assert feat_a.inbound_tx_count == 1
    assert feat_a.outbound_tx_count == 2
    assert feat_a.unique_counterparties == 3
    assert feat_a.total_inflow == 10.0
    assert feat_a.total_outflow == 6.0
    assert feat_a.net_flow == 4.0
    assert feat_a.residual_balance_ratio == 0.4
    assert feat_a.median_tx_value == 4.0
    assert feat_a.dormancy_period_seconds == 5 * 86400.0
    assert feat_a.bridge_interaction_count == 1
    assert feat_a.contract_interaction_ratio > 0.0
    assert feat_a.token_transfer_ratio > 0.0
    assert feat_a.utxo_avg_inputs == 0.0
    assert feat_a.address_reuse_count == 0


def test_bitcoin_utxo_features_and_address_reuse() -> None:
    case = InvestigationCase(
        investigation_id="TEST-FEAT-BTC",
        chain="bitcoin",
        seed_addresses=["bc1qA"],
        transactions=[
            NormalizedTransaction(
                tx_id="BTC-1",
                chain="bitcoin",
                timestamp=BASE,
                asset="BTC",
                inputs=[
                    UTXOEntry(address="bc1qA", value=1.5),
                    UTXOEntry(address="bc1qB", value=0.5),
                ],
                outputs=[
                    UTXOEntry(address="bc1qDest", value=1.8),
                    UTXOEntry(address="bc1qA", value=0.19),  # address reuse change
                ],
            )
        ],
    )
    index = InvestigationGraphIndex(case)
    feats = extract_all_wallet_features(index)
    feat_a = feats["bc1qA"]
    assert feat_a.utxo_avg_inputs == 2.0
    assert feat_a.utxo_avg_outputs == 2.0
    assert feat_a.address_reuse_count >= 1
    assert feat_a.contract_interaction_ratio == 0.0


def test_edge_only_graph_fallback_features() -> None:
    case = InvestigationCase(
        investigation_id="TEST-FEAT-EDGES",
        chain="ethereum",
        nodes=[GraphNode(node_id="0x1", address="0x1"), GraphNode(node_id="0x2", address="0x2")],
        edges=[
            GraphEdge(
                edge_id="E1",
                source="0x1",
                target="0x2",
                total_value=5.5,
                tx_count=2,
                relationship_status="inferred",
            )
        ],
    )
    index = InvestigationGraphIndex(case)
    feat_2 = extract_wallet_features(index, "0x2")
    assert feat_2.inbound_tx_count == 2
    assert feat_2.total_inflow == 5.5
