"""Tests for NetworkX Graph Engine, Multi-Hop Traversal, and Flow Analysis."""

from datetime import datetime, timezone
from decimal import Decimal
import pytest
from cryptotrace.connectors.fixtures.btc_samples import (
    BTC_SAMPLE_ADDRESS_1,
    BTC_SAMPLE_ADDRESS_2,
    BTC_SAMPLE_ADDRESS_5,
    BTC_SAMPLE_TX_1,
    BTC_SAMPLE_TX_2,
    BTC_SAMPLE_TX_3,
)
from cryptotrace.connectors.fixtures.eth_samples import (
    ETH_SAMPLE_ADDRESS_1,
    ETH_SAMPLE_ADDRESS_2,
    ETH_SAMPLE_ADDRESS_3,
    ETH_SAMPLE_ADDRESS_4,
    ETH_SAMPLE_TX_1,
    ETH_SAMPLE_TX_2,
    ETH_SAMPLE_TX_3,
)
from cryptotrace.graph.engine import BlockchainGraphEngine
from cryptotrace.graph.traversal import MultiHopTraversalEngine
from cryptotrace.normalization.bitcoin_normalizer import BitcoinNormalizer
from cryptotrace.normalization.ethereum_normalizer import EthereumNormalizer
from cryptotrace.schemas.common import BlockchainType, EdgeType, NodeType
from cryptotrace.schemas.graph import MultiHopTraversalRequest


def test_bitcoin_graph_no_false_attribution():
    """Bitcoin UTXO model must use Tx intermediate node to prevent false 1-to-1 input-output attribution."""
    tx = BitcoinNormalizer.normalize(BTC_SAMPLE_TX_1, provider_name="fixture_provider")
    engine = BlockchainGraphEngine()
    engine.add_canonical_transaction(tx, include_heuristics=True)

    g = engine.nx_graph
    tx_node_id = f"tx:{tx.tx_hash}"

    # Node types
    assert g.has_node(tx_node_id)
    assert g.nodes[tx_node_id]["node_type"] == NodeType.TRANSACTION

    # Check that inputs connect TO the transaction node
    in_edges = list(g.in_edges(tx_node_id, data=True))
    assert len(in_edges) == 2
    for _, _, data in in_edges:
        assert data["edge_type"] == EdgeType.UTXO_INPUT
        assert data["is_confirmed"] is True

    # Check that transaction node connects TO outputs
    out_edges = list(g.out_edges(tx_node_id, data=True))
    assert len(out_edges) == 2
    for _, _, data in out_edges:
        assert data["edge_type"] == EdgeType.UTXO_OUTPUT
        assert data["is_confirmed"] is True

    # Check that heuristic edges are explicitly marked
    heuristic_edges = [d for _, _, d in g.edges(data=True) if d.get("is_heuristic")]
    for h in heuristic_edges:
        assert h["is_confirmed"] is False
        assert h["edge_type"] == EdgeType.HEURISTIC_CO_SPEND


def test_ethereum_three_hop_traversal():
    """Verify 3-hop traversal from Address 1 -> Address 2 -> Address 3 -> Address 4."""
    tx1 = EthereumNormalizer.normalize(ETH_SAMPLE_TX_1, provider_name="fixture_provider")
    tx2 = EthereumNormalizer.normalize(ETH_SAMPLE_TX_2, provider_name="fixture_provider")
    tx3 = EthereumNormalizer.normalize(ETH_SAMPLE_TX_3, provider_name="fixture_provider")

    engine = BlockchainGraphEngine()
    engine.add_canonical_transaction(tx1)
    engine.add_canonical_transaction(tx2)
    engine.add_canonical_transaction(tx3)

    traversal_engine = MultiHopTraversalEngine(engine)

    # 1 Hop
    req1 = MultiHopTraversalRequest(
        start_address=ETH_SAMPLE_ADDRESS_1,
        blockchain=BlockchainType.ETHEREUM,
        max_hops=1,
    )
    res1 = traversal_engine.traverse(req1)
    node_ids1 = {n.id for n in res1.graph.nodes}
    assert ETH_SAMPLE_ADDRESS_1.lower() in node_ids1
    assert ETH_SAMPLE_ADDRESS_2.lower() in node_ids1
    assert ETH_SAMPLE_ADDRESS_3.lower() not in node_ids1

    # 3 Hops
    req3 = MultiHopTraversalRequest(
        start_address=ETH_SAMPLE_ADDRESS_1,
        blockchain=BlockchainType.ETHEREUM,
        max_hops=3,
    )
    res3 = traversal_engine.traverse(req3)
    node_ids3 = {n.id for n in res3.graph.nodes}
    assert ETH_SAMPLE_ADDRESS_1.lower() in node_ids3
    assert ETH_SAMPLE_ADDRESS_2.lower() in node_ids3
    assert ETH_SAMPLE_ADDRESS_3.lower() in node_ids3
    assert ETH_SAMPLE_ADDRESS_4.lower() in node_ids3
    assert len(res3.paths_found) >= 1


def test_disconnected_graph_branches():
    """Verify disconnected graph branches do not crash traversal or pollute connected nodes."""
    tx1 = EthereumNormalizer.normalize(ETH_SAMPLE_TX_1, provider_name="fixture_provider")

    # Independent disconnected transaction
    independent_tx = {
        "hash": "0x9999999999999999999999999999999999999999999999999999999999999999",
        "blockNumber": 100,
        "from": "0x1111111111111111111111111111111111111111",
        "to": "0x2222222222222222222222222222222222222222",
        "value": "1000000000000000000",
    }
    tx_indep = EthereumNormalizer.normalize(independent_tx, provider_name="fixture_provider")

    engine = BlockchainGraphEngine()
    engine.add_canonical_transaction(tx1)
    engine.add_canonical_transaction(tx_indep)

    traversal_engine = MultiHopTraversalEngine(engine)
    req = MultiHopTraversalRequest(
        start_address=ETH_SAMPLE_ADDRESS_1,
        blockchain=BlockchainType.ETHEREUM,
        max_hops=3,
    )
    res = traversal_engine.traverse(req)

    node_ids = {n.id for n in res.graph.nodes}
    assert "0x1111111111111111111111111111111111111111" not in node_ids
    assert "0x2222222222222222222222222222222222222222" not in node_ids


def test_graph_filtering_by_amount_and_time():
    tx1 = EthereumNormalizer.normalize(ETH_SAMPLE_TX_1, provider_name="fixture_provider")
    engine = BlockchainGraphEngine()
    engine.add_canonical_transaction(tx1)

    traversal_engine = MultiHopTraversalEngine(engine)

    # Filter min_amount > 5 ETH (tx1 amount is 2.5 ETH) -> Edge excluded
    req = MultiHopTraversalRequest(
        start_address=ETH_SAMPLE_ADDRESS_1,
        blockchain=BlockchainType.ETHEREUM,
        min_amount=Decimal("5.0"),
        max_hops=1,
    )
    res = traversal_engine.traverse(req)
    assert len(res.graph.edges) == 0

    # Filter with min_amount <= 2.5 ETH -> Edge included
    req2 = MultiHopTraversalRequest(
        start_address=ETH_SAMPLE_ADDRESS_1,
        blockchain=BlockchainType.ETHEREUM,
        min_amount=Decimal("2.0"),
        max_hops=1,
    )
    res2 = traversal_engine.traverse(req2)
    assert len(res2.graph.edges) == 1


def test_flow_analysis_accounting():
    tx1 = EthereumNormalizer.normalize(ETH_SAMPLE_TX_1, provider_name="fixture_provider")
    tx2 = EthereumNormalizer.normalize(ETH_SAMPLE_TX_2, provider_name="fixture_provider")

    engine = BlockchainGraphEngine()
    engine.add_canonical_transaction(tx1)
    engine.add_canonical_transaction(tx2)

    traversal_engine = MultiHopTraversalEngine(engine)
    # Target address is Address 2 (received 2.5 ETH, sent 5000 USDT)
    flow = traversal_engine._compute_flow_analysis(ETH_SAMPLE_ADDRESS_2.lower(), BlockchainType.ETHEREUM)

    assert flow.target_address == ETH_SAMPLE_ADDRESS_2.lower()
    assert flow.overall_metrics.total_inflow == Decimal("2.5")
    assert flow.overall_metrics.total_outflow == Decimal("5000.000000")
    assert flow.overall_metrics.inflow_tx_count == 1
    assert flow.overall_metrics.outflow_tx_count == 1
