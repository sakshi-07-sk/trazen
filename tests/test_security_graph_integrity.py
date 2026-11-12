"""Unit & negative tests for NetworkX graph poisoning, Bitcoin UTXO, and ERC-20 graph integrity."""

from __future__ import annotations

from decimal import Decimal

import pytest

from cryptotrace.connectors.fixtures.btc_samples import (
    BTC_SAMPLE_ADDRESS_1,
    BTC_SAMPLE_TX_1,
    BTC_SAMPLE_TX_2,
)
from cryptotrace.connectors.fixtures.eth_samples import (
    ETH_SAMPLE_ADDRESS_1,
    ETH_SAMPLE_TX_1,
    ETH_SAMPLE_TX_2,
    ETH_SAMPLE_TX_3,
)
from cryptotrace.graph.engine import BlockchainGraphEngine
from cryptotrace.graph.traversal import MultiHopTraversalEngine
from cryptotrace.normalization.bitcoin_normalizer import BitcoinNormalizer
from cryptotrace.normalization.ethereum_normalizer import EthereumNormalizer
from cryptotrace.schemas.common import BlockchainType
from cryptotrace.schemas.graph import MultiHopTraversalRequest
from cryptotrace.schemas.security_common import FindingCategory, ValidationStatus
from cryptotrace.schemas.security_inputs import GraphEdgeInput, GraphNodeInput, TransactionRecord
from cryptotrace.services.security.adapters import (
    canonical_tx_to_security_records,
    transaction_graph_to_security_inputs,
)
from cryptotrace.services.security.graph_integrity import GraphIntegrityAnalyzer


@pytest.mark.unit
def test_detects_duplicate_missing_reversed_and_conflicting_graph_edges() -> None:
    analyzer = GraphIntegrityAnalyzer()
    a = "0x1111111111111111111111111111111111111111"
    b = "0x2222222222222222222222222222222222222222"
    c = "0x3333333333333333333333333333333333333333"

    tx1 = "0x" + "1" * 64
    tx2 = "0x" + "2" * 64

    nodes = [
        GraphNodeInput(node_id=a, chain="ethereum"),
        GraphNodeInput(node_id=b, chain="ethereum"),
        GraphNodeInput(node_id=c, chain="ethereum"),
    ]
    evidence = [
        TransactionRecord(
            tx_hash=tx1,
            chain="ethereum",
            block_number=100,
            from_address=a,
            to_address=b,
            amount=Decimal("5.0"),
            asset_symbol="ETH",
            provenance_id="prov-1",
        ),
        TransactionRecord(
            tx_hash=tx2,
            chain="ethereum",
            block_number=101,
            from_address=b,
            to_address=c,
            amount=Decimal("2.0"),
            asset_symbol="ETH",
            provenance_id="prov-2",
        ),
    ]
    verified = [
        TransactionRecord(
            tx_hash=tx1,
            chain="ethereum",
            block_number=100,
            from_address=a,
            to_address=b,
            amount=Decimal("1.0"),
            asset_symbol="ETH",
        )
    ]

    edges = [
        GraphEdgeInput(
            edge_id="e1",
            source=a,
            target=b,
            tx_hash=tx1,
            chain="ethereum",
            block_number=100,
            asset="ETH",
            amount=Decimal("5.0"),
            provenance_ref="prov-1",
        ),
        GraphEdgeInput(
            edge_id="e2",
            source=a,
            target=b,
            tx_hash=tx1,
            chain="ethereum",
            block_number=100,
            asset="ETH",
            amount=Decimal("5.0"),
            provenance_ref="prov-1",
        ),
        GraphEdgeInput(
            edge_id="e3",
            source=c,
            target=b,
            tx_hash=tx2,
            chain="polygon",
            block_number=101,
            asset="ETH",
        ),
        GraphEdgeInput(
            edge_id="e4",
            source=a,
            target=c,
            tx_hash=None,
            chain="ethereum",
        ),
    ]

    summary, findings = analyzer.analyze(
        investigation_id="inv-graph-1",
        nodes=nodes,
        edges=edges,
        evidence_transactions=evidence,
        verified_transactions=verified,
    )

    assert not summary.is_integrity_clean
    assert summary.duplicate_edge_count == 1
    assert summary.flagged_edge_count == 4
    types = {f.finding_type for f in findings}
    assert "duplicate_graph_edge" in types
    assert "graph_edge_chain_mismatch" in types
    assert "unsupported_graph_edge" in types
    assert any(f.validation_status == ValidationStatus.CONFLICTING for f in findings)


@pytest.mark.unit
def test_unusual_valid_cycle_graph_is_not_falsely_labeled_decoy() -> None:
    """Negative test: unusual topology with valid verified evidence must remain clean."""
    analyzer = GraphIntegrityAnalyzer()
    a = "0x1111111111111111111111111111111111111111"
    b = "0x2222222222222222222222222222222222222222"
    c = "0x3333333333333333333333333333333333333333"

    tx1, tx2, tx3 = "0x" + "1" * 64, "0x" + "2" * 64, "0x" + "3" * 64
    nodes = [
        GraphNodeInput(node_id=a, chain="ethereum"),
        GraphNodeInput(node_id=b, chain="ethereum"),
        GraphNodeInput(node_id=c, chain="ethereum"),
    ]
    evidence = [
        TransactionRecord(
            tx_hash=tx1,
            chain="ethereum",
            block_number=10,
            from_address=a,
            to_address=b,
            amount=Decimal("1"),
            asset_symbol="ETH",
            provenance_id="p1",
        ),
        TransactionRecord(
            tx_hash=tx2,
            chain="ethereum",
            block_number=11,
            from_address=b,
            to_address=c,
            amount=Decimal("1"),
            asset_symbol="ETH",
            provenance_id="p2",
        ),
        TransactionRecord(
            tx_hash=tx3,
            chain="ethereum",
            block_number=12,
            from_address=c,
            to_address=a,
            amount=Decimal("1"),
            asset_symbol="ETH",
            provenance_id="p3",
        ),
    ]
    edges = [
        GraphEdgeInput(
            edge_id="e1",
            source=a,
            target=b,
            tx_hash=tx1,
            chain="ethereum",
            block_number=10,
            asset="ETH",
            amount=Decimal("1"),
            provenance_ref="p1",
        ),
        GraphEdgeInput(
            edge_id="e2",
            source=b,
            target=c,
            tx_hash=tx2,
            chain="ethereum",
            block_number=11,
            asset="ETH",
            amount=Decimal("1"),
            provenance_ref="p2",
        ),
        GraphEdgeInput(
            edge_id="e3",
            source=c,
            target=a,
            tx_hash=tx3,
            chain="ethereum",
            block_number=12,
            asset="ETH",
            amount=Decimal("1"),
            provenance_ref="p3",
        ),
    ]

    summary, findings = analyzer.analyze(
        investigation_id="inv-graph-clean",
        nodes=nodes,
        edges=edges,
        evidence_transactions=evidence,
        verified_transactions=evidence,
        require_provenance_ref=True,
    )
    assert summary.is_integrity_clean
    assert summary.validated_edge_count == 3
    assert findings == []
    assert not any(f.finding_category == FindingCategory.DECOY_EDGE for f in findings)


@pytest.mark.unit
def test_legitimate_bitcoin_utxo_graph_with_heuristics_produces_no_false_violations() -> None:
    """Verify Role 1 Bitcoin multi-input/multi-output UTXO + heuristic co-spend graph passes cleanly."""
    tx1 = BitcoinNormalizer.normalize(BTC_SAMPLE_TX_1, provider_name="fixture_provider")
    tx2 = BitcoinNormalizer.normalize(BTC_SAMPLE_TX_2, provider_name="fixture_provider")

    engine = BlockchainGraphEngine()
    engine.add_canonical_transaction(tx1, include_heuristics=True)
    engine.add_canonical_transaction(tx2, include_heuristics=True)

    trav = MultiHopTraversalEngine(engine)
    res = trav.traverse(
        MultiHopTraversalRequest(
            start_address=BTC_SAMPLE_ADDRESS_1,
            blockchain=BlockchainType.BITCOIN,
            max_hops=2,
            include_heuristics=True,
        )
    )

    nodes, edges = transaction_graph_to_security_inputs(res.graph)
    evidence = canonical_tx_to_security_records(tx1) + canonical_tx_to_security_records(tx2)

    analyzer = GraphIntegrityAnalyzer()
    summary, findings = analyzer.analyze(
        investigation_id="inv-btc-clean",
        nodes=nodes,
        edges=edges,
        evidence_transactions=evidence,
    )
    assert summary.is_integrity_clean, f"Unexpected findings: {findings}"
    assert summary.flagged_edge_count == 0
    assert summary.validated_edge_count == len(edges)
    assert findings == []


@pytest.mark.unit
def test_legitimate_ethereum_native_and_erc20_graph_produces_no_false_violations() -> None:
    """Verify Role 1 Ethereum native + ERC-20 TokenTransfer graph passes cleanly."""
    tx1 = EthereumNormalizer.normalize(ETH_SAMPLE_TX_1, provider_name="fixture_provider")
    tx2 = EthereumNormalizer.normalize(ETH_SAMPLE_TX_2, provider_name="fixture_provider")
    tx3 = EthereumNormalizer.normalize(ETH_SAMPLE_TX_3, provider_name="fixture_provider")

    engine = BlockchainGraphEngine()
    engine.add_canonical_transaction(tx1)
    engine.add_canonical_transaction(tx2)
    engine.add_canonical_transaction(tx3)

    trav = MultiHopTraversalEngine(engine)
    res = trav.traverse(
        MultiHopTraversalRequest(
            start_address=ETH_SAMPLE_ADDRESS_1,
            blockchain=BlockchainType.ETHEREUM,
            max_hops=3,
            include_heuristics=True,
        )
    )

    nodes, edges = transaction_graph_to_security_inputs(res.graph)
    evidence = (
        canonical_tx_to_security_records(tx1)
        + canonical_tx_to_security_records(tx2)
        + canonical_tx_to_security_records(tx3)
    )

    analyzer = GraphIntegrityAnalyzer()
    summary, findings = analyzer.analyze(
        investigation_id="inv-eth-clean",
        nodes=nodes,
        edges=edges,
        evidence_transactions=evidence,
    )
    assert summary.is_integrity_clean, f"Unexpected findings: {findings}"
    assert summary.flagged_edge_count == 0
    assert summary.validated_edge_count == len(edges)
    assert findings == []

