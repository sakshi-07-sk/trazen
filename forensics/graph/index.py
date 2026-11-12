"""Single-pass indexed graph and transaction representation for fast forensic analysis."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

import networkx as nx

from forensics.schemas.input import (
    ChainType,
    EntityLabel,
    GraphEdge,
    GraphNode,
    InvestigationCase,
    NormalizedTransaction,
    RelationshipStatus,
)


@dataclass(frozen=True)
class TransferLeg:
    """Normalized directed value transfer between two addresses for a transaction."""

    tx_id: str
    chain: ChainType
    timestamp: datetime
    sender: str
    receiver: str
    value: float
    fee: float
    relationship_status: RelationshipStatus
    is_contract_call: bool = False
    is_token_transfer: bool = False
    is_bridge_interaction: bool = False
    is_utxo: bool = False


class InvestigationGraphIndex:
    """Caches normalized adjacency, UTXO participation, labels, and reachability per case."""

    def __init__(self, case: InvestigationCase) -> None:
        self.case = case
        self.chain: ChainType = case.chain
        self.tx_by_id: Dict[str, NormalizedTransaction] = {}
        self.node_by_address: Dict[str, GraphNode] = {}
        self.labels_by_address: Dict[str, List[EntityLabel]] = defaultdict(list)
        self.inbound_legs: Dict[str, List[TransferLeg]] = defaultdict(list)
        self.outbound_legs: Dict[str, List[TransferLeg]] = defaultdict(list)
        self.utxo_txs_by_address: Dict[str, List[NormalizedTransaction]] = defaultdict(list)
        self.all_addresses: Set[str] = set()
        self.nx_graph: nx.DiGraph = nx.DiGraph()
        self.edge_lookup: Dict[Tuple[str, str], GraphEdge] = {}

        self._feature_cache: Dict[str, object] = {}
        self._shortest_paths_from_seeds: Optional[Dict[str, List[str]]] = None

        self._build_index()

    def _build_index(self) -> None:
        for addr in self.case.seed_addresses:
            self.all_addresses.add(addr)

        for label in self.case.labels:
            self.labels_by_address[label.address].append(label)
            self.all_addresses.add(label.address)

        for node in self.case.nodes:
            self.node_by_address[node.address] = node
            self.all_addresses.add(node.address)
            for lbl in node.labels:
                self.labels_by_address[node.address].append(lbl)
            self.nx_graph.add_node(
                node.address,
                observed_in_full=node.observed_in_full,
                missing_neighbors_estimated=node.missing_neighbors_estimated,
                role_hint=node.role_hint,
            )

        for edge in self.case.edges:
            self.edge_lookup[(edge.source, edge.target)] = edge
            self.all_addresses.add(edge.source)
            self.all_addresses.add(edge.target)
            self.nx_graph.add_edge(
                edge.source,
                edge.target,
                edge_id=edge.edge_id,
                total_value=edge.total_value,
                tx_count=edge.tx_count,
                tx_ids=list(edge.tx_ids),
                relationship_status=edge.relationship_status,
                confidence=edge.confidence,
                inference_reason=edge.inference_reason,
            )

        sorted_txs = sorted(self.case.transactions, key=lambda t: t.timestamp)
        for tx in sorted_txs:
            self.tx_by_id[tx.tx_id] = tx
            self._index_transaction(tx)

        # Ensure graph contains edges inferred from transactions even if Role 1 omitted GraphEdges
        for addr, legs in self.outbound_legs.items():
            for leg in legs:
                if not self.nx_graph.has_edge(leg.sender, leg.receiver):
                    self.nx_graph.add_edge(
                        leg.sender,
                        leg.receiver,
                        edge_id=f"AUTO-{leg.tx_id}",
                        total_value=leg.value,
                        tx_count=1,
                        tx_ids=[leg.tx_id],
                        relationship_status=leg.relationship_status,
                        confidence=1.0 if leg.relationship_status == "confirmed" else 0.7,
                        inference_reason=None,
                    )
                else:
                    # Ensure tx_id is tracked if edge was pre-populated without it
                    data = self.nx_graph[leg.sender][leg.receiver]
                    if leg.tx_id not in data.get("tx_ids", []):
                        data["tx_ids"].append(leg.tx_id)
                        data["total_value"] = float(data.get("total_value", 0.0)) + leg.value
                        data["tx_count"] = int(data.get("tx_count", 0)) + 1

        for addr in self.all_addresses:
            if addr not in self.nx_graph:
                self.nx_graph.add_node(addr, observed_in_full=True, missing_neighbors_estimated=0)
            self.inbound_legs[addr].sort(key=lambda leg: leg.timestamp)
            self.outbound_legs[addr].sort(key=lambda leg: leg.timestamp)

    def _index_transaction(self, tx: NormalizedTransaction) -> None:
        if tx.inputs or tx.outputs:
            self._index_utxo_transaction(tx)
            return

        if tx.from_address and tx.to_address:
            leg = TransferLeg(
                tx_id=tx.tx_id,
                chain=tx.chain,
                timestamp=tx.timestamp,
                sender=tx.from_address,
                receiver=tx.to_address,
                value=tx.value,
                fee=tx.fee,
                relationship_status=tx.relationship_status,
                is_contract_call=tx.is_contract_call,
                is_token_transfer=tx.is_token_transfer,
                is_bridge_interaction=tx.is_bridge_interaction,
                is_utxo=False,
            )
            self.outbound_legs[tx.from_address].append(leg)
            self.inbound_legs[tx.to_address].append(leg)
            self.all_addresses.add(tx.from_address)
            self.all_addresses.add(tx.to_address)

    def _index_utxo_transaction(self, tx: NormalizedTransaction) -> None:
        input_addrs: List[str] = []
        seen_in: Set[str] = set()
        total_in = 0.0
        for inp in tx.inputs:
            self.all_addresses.add(inp.address)
            total_in += inp.value
            if inp.address not in seen_in:
                seen_in.add(inp.address)
                input_addrs.append(inp.address)
                self.utxo_txs_by_address[inp.address].append(tx)

        output_addrs: Set[str] = set()
        for out in tx.outputs:
            self.all_addresses.add(out.address)
            if out.address not in output_addrs:
                output_addrs.add(out.address)
                if out.address not in seen_in:
                    self.utxo_txs_by_address[out.address].append(tx)

        if not tx.inputs or not tx.outputs:
            # Partial UTXO tx fallback
            if tx.from_address and tx.to_address:
                leg = TransferLeg(
                    tx_id=tx.tx_id,
                    chain=tx.chain,
                    timestamp=tx.timestamp,
                    sender=tx.from_address,
                    receiver=tx.to_address,
                    value=tx.value,
                    fee=tx.fee,
                    relationship_status=tx.relationship_status,
                    is_utxo=True,
                )
                self.outbound_legs[tx.from_address].append(leg)
                self.inbound_legs[tx.to_address].append(leg)
            return

        # Aggregate input shares per unique input address so flow conservation holds
        in_by_addr: Dict[str, float] = defaultdict(float)
        for inp in tx.inputs:
            in_by_addr[inp.address] += inp.value

        denom = total_in if total_in > 0 else float(len(in_by_addr))
        for out in tx.outputs:
            for sender, sender_val in in_by_addr.items():
                if sender == out.address:
                    # Self-change output is not an external transfer leg,
                    # though it remains in tx.outputs for peel-chain & reuse inspection.
                    continue
                share = (sender_val / denom) if total_in > 0 else (1.0 / denom)
                allocated_value = out.value * share
                # Multi-input UTXO attribution between specific input & output is inferred unless 1-input
                rel_status: RelationshipStatus = (
                    tx.relationship_status if len(in_by_addr) == 1 else "inferred"
                )
                leg = TransferLeg(
                    tx_id=tx.tx_id,
                    chain=tx.chain,
                    timestamp=tx.timestamp,
                    sender=sender,
                    receiver=out.address,
                    value=allocated_value,
                    fee=tx.fee,
                    relationship_status=rel_status,
                    is_utxo=True,
                )
                self.outbound_legs[sender].append(leg)
                self.inbound_legs[out.address].append(leg)

    def get_labels(self, address: str) -> List[EntityLabel]:
        return self.labels_by_address.get(address, [])

    def get_primary_label(self, address: str) -> Optional[EntityLabel]:
        labels = self.get_labels(address)
        if not labels:
            return None
        return sorted(labels, key=lambda l: (l.verified, l.confidence), reverse=True)[0]

    def has_category(self, address: str, categories: Set[str]) -> bool:
        return any(lbl.category.lower() in categories for lbl in self.get_labels(address))

    def shortest_paths_from_seeds(self) -> Dict[str, List[str]]:
        """Cached BFS shortest paths from seed addresses to all reachable addresses."""
        if self._shortest_paths_from_seeds is not None:
            return self._shortest_paths_from_seeds

        paths: Dict[str, List[str]] = {}
        seeds = self.case.seed_addresses or self._infer_root_addresses()
        queue: deque[List[str]] = deque()
        for seed in seeds:
            if seed in self.nx_graph:
                paths[seed] = [seed]
                queue.append([seed])

        while queue:
            path = queue.popleft()
            curr = path[-1]
            for nxt in self.nx_graph.successors(curr):
                if nxt not in paths:
                    new_path = path + [nxt]
                    paths[nxt] = new_path
                    queue.append(new_path)

        self._shortest_paths_from_seeds = paths
        return paths

    def _infer_root_addresses(self) -> List[str]:
        roots = [n for n in self.nx_graph.nodes if self.nx_graph.in_degree(n) == 0]
        return roots if roots else list(self.nx_graph.nodes)[:1]

    def confirmed_edge_ratio(self) -> float:
        edges = list(self.nx_graph.edges(data=True))
        if not edges:
            return 0.0
        confirmed = sum(1 for _, _, data in edges if data.get("relationship_status") == "confirmed")
        return confirmed / len(edges)

    def compute_investigation_coverage(self) -> Tuple[float, List[str]]:
        """Compute [0, 1] graph observation coverage and explain missing-data limitations."""
        notes: List[str] = list(self.case.missing_data_notes)
        nodes = list(self.nx_graph.nodes(data=True))
        if not nodes:
            return 0.0, ["No graph nodes or transactions observed."]

        observed_nodes = sum(1 for _, data in nodes if data.get("observed_in_full", True))
        node_obs_ratio = observed_nodes / len(nodes)

        missing_neighbors = sum(int(data.get("missing_neighbors_estimated", 0)) for _, data in nodes)
        edge_count = max(1, self.nx_graph.number_of_edges())
        neighbor_completeness = edge_count / (edge_count + missing_neighbors)

        coverage = 0.55 * node_obs_ratio + 0.45 * neighbor_completeness
        if not self.case.is_graph_complete:
            coverage *= 0.85
            notes.append("Investigation graph is marked incomplete by upstream ingestion.")

        if observed_nodes < len(nodes):
            notes.append(
                f"{len(nodes) - observed_nodes} of {len(nodes)} nodes were not observed in full."
            )
        if missing_neighbors > 0:
            notes.append(
                f"Estimated {missing_neighbors} unexpanded neighbor relationships exist beyond trace boundary."
            )
        if not self.case.transactions:
            coverage *= 0.6
            notes.append("No detailed normalized transactions provided; relying on graph edges only.")

        return max(0.0, min(1.0, round(coverage, 4))), notes

    def min_hop_distance_to_risk_indicator(
        self, address: str, max_hops: int = 4
    ) -> Optional[Tuple[int, str, EntityLabel]]:
        """BFS over undirected/directed neighborhood to nearest high/critical risk label."""
        visited: Set[str] = {address}
        queue: deque[Tuple[str, int]] = deque([(address, 0)])
        while queue:
            curr, dist = queue.popleft()
            for lbl in self.get_labels(curr):
                if lbl.risk_indicator in {"high", "critical"}:
                    return dist, curr, lbl
            if dist >= max_hops:
                continue
            neighbors = set(self.nx_graph.successors(curr)) | set(self.nx_graph.predecessors(curr))
            for nxt in neighbors:
                if nxt not in visited:
                    visited.add(nxt)
                    queue.append((nxt, dist + 1))
        return None
