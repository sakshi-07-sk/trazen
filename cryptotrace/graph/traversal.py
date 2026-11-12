"""Multi-Hop Transaction Traversal, Subgraph Extraction, and Flow Analysis."""

from collections import deque
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Set, Tuple
import networkx as nx

from cryptotrace.db.models.graph import GraphEdgeModel, GraphNodeModel, InvestigationPathModel
from cryptotrace.graph.engine import BlockchainGraphEngine
from cryptotrace.schemas.common import BlockchainType, EdgeType, NodeType
from cryptotrace.schemas.graph import (
    FlowAnalysis,
    FlowMetric,
    GraphEdge,
    GraphNode,
    MultiHopTraversalRequest,
    MultiHopTraversalResult,
    TransactionGraph,
)


class MultiHopTraversalEngine:
    """Performs bounded multi-hop graph traversals and flow accounting."""

    def __init__(self, engine: BlockchainGraphEngine) -> None:
        self.engine = engine
        self.g: nx.MultiDiGraph = engine.nx_graph

    def traverse(self, req: MultiHopTraversalRequest) -> MultiHopTraversalResult:
        """Execute multi-hop exploration from seed address with constraints."""
        seed = req.start_address.lower() if req.blockchain == BlockchainType.ETHEREUM else req.start_address

        if not self.g.has_node(seed):
            # Address has no transactions loaded
            empty_graph = TransactionGraph(root_node_id=seed, max_hops=req.max_hops, node_count=0, edge_count=0)
            return MultiHopTraversalResult(
                seed_address=seed,
                blockchain=req.blockchain,
                depth_reached=0,
                graph=empty_graph,
                flow_analysis=FlowAnalysis(
                    target_address=seed,
                    blockchain=req.blockchain,
                    overall_metrics=FlowMetric(),
                ),
                paths_found=[],
            )

        # BFS expansion
        visited_nodes: Set[str] = {seed}
        # Queue stores: (current_node, current_hop_depth, path)
        queue = deque([(seed, 0, [seed])])
        discovered_paths: List[List[str]] = []

        # Bitcoin graphs have address -> tx_node -> address.
        # In Bitcoin, an entity hop consists of (Address -> Tx -> Address), so we step through.
        effective_max_depth = req.max_hops * 2 if req.blockchain == BlockchainType.BITCOIN else req.max_hops

        while queue:
            curr, depth, path = queue.popleft()
            if depth >= effective_max_depth:
                continue

            neighbors_to_explore: List[Tuple[str, Dict[str, Any]]] = []

            # Forward exploration (outgoing)
            if req.direction in ("forward", "both"):
                for _, target, edge_data in self.g.out_edges(curr, data=True):
                    if self._matches_filters(edge_data, req):
                        neighbors_to_explore.append((target, edge_data))

            # Backward exploration (incoming)
            if req.direction in ("backward", "both"):
                for source, _, edge_data in self.g.in_edges(curr, data=True):
                    if self._matches_filters(edge_data, req):
                        neighbors_to_explore.append((source, edge_data))

            for neighbor, _ in neighbors_to_explore:
                if neighbor not in path:  # avoid cycles
                    new_path = path + [neighbor]
                    visited_nodes.add(neighbor)
                    discovered_paths.append(new_path)
                    if len(discovered_paths) < 200:
                        queue.append((neighbor, depth + 1, new_path))

        # Extract induced subgraph
        subgraph = self.g.subgraph(visited_nodes).copy()

        # Build GraphNode and GraphEdge schemas
        nodes: List[GraphNode] = []
        for n, data in subgraph.nodes(data=True):
            node_schema = GraphNode(
                id=n,
                node_type=data.get("node_type", NodeType.WALLET),
                label=data.get("label", n),
                blockchain=data.get("blockchain", req.blockchain),
                chain_id=data.get("chain_id", "mainnet"),
                properties=data.get("properties", {}),
                first_seen=data.get("first_seen"),
                last_seen=data.get("last_seen"),
            )
            nodes.append(node_schema)

        edges: List[GraphEdge] = []
        for u, v, k, data in subgraph.edges(keys=True, data=True):
            if not self._matches_filters(data, req):
                continue
            edge_schema = GraphEdge(
                id=data.get("id", str(k)),
                source=u,
                target=v,
                edge_type=data.get("edge_type", EdgeType.CONFIRMED_TRANSFER),
                is_confirmed=data.get("is_confirmed", True),
                is_heuristic=data.get("is_heuristic", False),
                amount=data.get("amount", Decimal("0")),
                asset_symbol=data.get("asset_symbol", "NATIVE"),
                tx_hash=data.get("tx_hash", ""),
                block_number=data.get("block_number"),
                timestamp=data.get("timestamp"),
                evidence_reference=data.get("evidence_reference", ""),
                properties=data.get("properties", {}),
            )
            edges.append(edge_schema)

        tx_graph = TransactionGraph(
            root_node_id=seed,
            max_hops=req.max_hops,
            nodes=nodes,
            edges=edges,
            node_count=len(nodes),
            edge_count=len(edges),
            filters_applied={
                "min_amount": str(req.min_amount) if req.min_amount else None,
                "max_amount": str(req.max_amount) if req.max_amount else None,
                "start_time": req.start_time.isoformat() if req.start_time else None,
                "end_time": req.end_time.isoformat() if req.end_time else None,
                "direction": req.direction,
                "include_heuristics": req.include_heuristics,
            },
        )

        flow_analysis = self._compute_flow_analysis(seed, req.blockchain)

        return MultiHopTraversalResult(
            seed_address=seed,
            blockchain=req.blockchain,
            depth_reached=min(req.max_hops, max([len(p) - 1 for p in discovered_paths] or [0])),
            graph=tx_graph,
            flow_analysis=flow_analysis,
            paths_found=discovered_paths[:50],  # cap to top 50 paths
        )

    def _matches_filters(self, edge_data: Dict[str, Any], req: MultiHopTraversalRequest) -> bool:
        """Check if edge meets all traversal criteria."""
        if not req.include_heuristics and edge_data.get("is_heuristic", False):
            return False

        amount = edge_data.get("amount", Decimal("0"))
        if req.min_amount is not None and amount < req.min_amount:
            return False
        if req.max_amount is not None and amount > req.max_amount:
            return False

        edge_time = edge_data.get("timestamp")
        if edge_time:
            if req.start_time and edge_time < req.start_time:
                return False
            if req.end_time and edge_time > req.end_time:
                return False

        if req.asset_filter:
            if edge_data.get("asset_symbol") != req.asset_filter:
                return False

        return True

    def _compute_flow_analysis(self, seed: str, blockchain: BlockchainType) -> FlowAnalysis:
        """Compute aggregated inflow and outflow accounting for seed node."""
        total_inflow = Decimal("0")
        total_outflow = Decimal("0")
        in_tx_count = 0
        out_tx_count = 0
        counterparties_in: Set[str] = set()
        counterparties_out: Set[str] = set()
        sources_map: Dict[str, Decimal] = {}
        dest_map: Dict[str, Decimal] = {}

        if self.g.has_node(seed):
            # Inflow
            for src, _, data in self.g.in_edges(seed, data=True):
                if data.get("is_confirmed", True):
                    amt = data.get("amount", Decimal("0"))
                    total_inflow += amt
                    in_tx_count += 1
                    counterparties_in.add(src)
                    sources_map[src] = sources_map.get(src, Decimal("0")) + amt

            # Outflow
            for _, dst, data in self.g.out_edges(seed, data=True):
                if data.get("is_confirmed", True):
                    amt = data.get("amount", Decimal("0"))
                    total_outflow += amt
                    out_tx_count += 1
                    counterparties_out.add(dst)
                    dest_map[dst] = dest_map.get(dst, Decimal("0")) + amt

        top_in = [
            {"source": k, "amount": str(v)}
            for k, v in sorted(sources_map.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        top_out = [
            {"destination": k, "amount": str(v)}
            for k, v in sorted(dest_map.items(), key=lambda x: x[1], reverse=True)[:5]
        ]

        metrics = FlowMetric(
            total_inflow=total_inflow,
            total_outflow=total_outflow,
            net_flow=total_inflow - total_outflow,
            inflow_tx_count=in_tx_count,
            outflow_tx_count=out_tx_count,
            unique_counterparties_in=len(counterparties_in),
            unique_counterparties_out=len(counterparties_out),
        )

        return FlowAnalysis(
            target_address=seed,
            blockchain=blockchain,
            overall_metrics=metrics,
            top_inflow_sources=top_in,
            top_outflow_destinations=top_out,
        )

    def to_db_models(
        self, investigation_id: str, graph: TransactionGraph, paths: List[List[str]]
    ) -> Tuple[List[GraphNodeModel], List[GraphEdgeModel], List[InvestigationPathModel]]:
        """Convert graph schema into database ORM models."""
        node_models = [
            GraphNodeModel(
                investigation_id=investigation_id,
                node_id=n.id,
                node_type=n.node_type.value,
                label=n.label,
                blockchain=n.blockchain.value,
                chain_id=n.chain_id,
                properties=n.properties,
            )
            for n in graph.nodes
        ]

        edge_models = [
            GraphEdgeModel(
                investigation_id=investigation_id,
                source_id=e.source,
                target_id=e.target,
                edge_type=e.edge_type.value,
                is_confirmed=e.is_confirmed,
                is_heuristic=e.is_heuristic,
                amount=e.amount,
                asset_symbol=e.asset_symbol,
                tx_hash=e.tx_hash,
                evidence_reference=e.evidence_reference,
                properties=e.properties,
            )
            for e in graph.edges
        ]

        path_models = [
            InvestigationPathModel(
                investigation_id=investigation_id,
                path_nodes=p,
                hop_count=len(p) - 1,
                total_amount=Decimal("0"),
                summary_info={"hops": len(p) - 1},
            )
            for p in paths[:20]
        ]

        return node_models, edge_models, path_models
