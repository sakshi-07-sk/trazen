"""NetworkX-backed graph integrity and decoy/graph-poisoning detection engine."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

import networkx as nx

from cryptotrace.schemas.findings import SecurityFinding
from cryptotrace.schemas.security_common import (
    EpistemicLabel,
    EvidenceReference,
    FindingCategory,
    Severity,
    ValidationStatus,
)
from cryptotrace.schemas.security_inputs import GraphEdgeInput, GraphNodeInput, TransactionRecord
from cryptotrace.services.security.address_similarity import (
    normalize_chain_name,
    validate_and_normalize_address,
)


def _to_decimal(val: object) -> Decimal | None:
    if val is None:
        return None
    try:
        dec = Decimal(str(val))
        return dec if dec.is_finite() else None
    except (InvalidOperation, ValueError, TypeError):
        return None


def _norm_tx_hash(tx_hash: str | None) -> str:
    return (tx_hash or "").strip().lower()


def _norm_endpoint(address: str, chain: str) -> str:
    raw = address.strip()
    if not raw:
        return ""
    low = raw.lower()
    if low.startswith("tx:") or low.startswith("coinbase") or low.startswith("op_return:") or low == "unparsed_output":
        return low
    if not chain:
        return low
    res = validate_and_normalize_address(raw, chain)
    return res.normalized_address if res.is_valid else low


def _select_matching_evidence(
    edge: GraphEdgeInput,
    candidates: list[TransactionRecord],
    e_chain: str,
    e_src: str,
    e_dst: str,
    e_contract: str,
    e_asset: str,
) -> TransactionRecord:
    """Select the closest matching evidence record when a tx_hash expands to multiple transfers/UTXOs."""
    if len(candidates) == 1:
        return candidates[0]

    edge_amt = _to_decimal(edge.amount)
    best_tx = candidates[0]
    best_score = -1

    for cand in candidates:
        c_chain = normalize_chain_name(cand.chain)
        c_src = _norm_endpoint(cand.from_address or "", c_chain)
        c_dst = _norm_endpoint(cand.to_address or "", c_chain)
        c_contract = (cand.token_contract or "").strip().lower()
        c_asset = (cand.asset_symbol or "").strip().upper()
        c_amt = _to_decimal(cand.amount)

        score = 0
        if c_src == e_src:
            score += 4
        if c_dst == e_dst:
            score += 4
        if c_src == e_dst and c_dst == e_src:
            score += 1  # reversed-direction candidate still helps catch reversals
        if edge.log_index is not None and cand.log_index is not None and edge.log_index == cand.log_index:
            score += 3
        if edge.vout is not None and cand.vout is not None and edge.vout == cand.vout:
            score += 3
        if e_contract and c_contract and e_contract == c_contract:
            score += 2
        if e_asset and c_asset and e_asset == c_asset:
            score += 2
        if edge_amt is not None and c_amt is not None and edge_amt == c_amt:
            score += 2

        if score > best_score:
            best_score = score
            best_tx = cand

    return best_tx


@dataclass(frozen=True)
class GraphIntegritySummary:
    """Summary of the analyzed NetworkX investigation graph and integrity checks."""

    node_count: int
    edge_count: int
    validated_edge_count: int
    flagged_edge_count: int
    duplicate_edge_count: int
    is_integrity_clean: bool


class GraphIntegrityAnalyzer:
    """Validates graph edges against underlying transaction and provenance evidence using NetworkX."""

    def build_networkx_graph(
        self,
        nodes: list[GraphNodeInput],
        edges: list[GraphEdgeInput],
    ) -> nx.MultiDiGraph:
        """Construct a NetworkX MultiDiGraph compatible with Role 1/Role 2 graph structures."""
        graph = nx.MultiDiGraph()
        for node in nodes:
            chain = normalize_chain_name(node.chain)
            norm_id = _norm_endpoint(node.node_id, chain)
            graph.add_node(
                norm_id,
                raw_id=node.node_id,
                chain=chain or None,
                node_type=node.node_type,
                label=node.label,
                **node.metadata,
            )

        for edge in edges:
            chain = normalize_chain_name(edge.chain)
            src = _norm_endpoint(edge.source, chain)
            dst = _norm_endpoint(edge.target, chain)
            graph.add_edge(
                src,
                dst,
                key=edge.edge_id,
                edge_id=edge.edge_id,
                tx_hash=_norm_tx_hash(edge.tx_hash),
                chain=chain or None,
                edge_type=edge.edge_type,
                is_confirmed=edge.is_confirmed,
                is_heuristic=edge.is_heuristic,
                block_number=edge.block_number,
                asset=edge.asset,
                token_contract=(edge.token_contract or "").strip().lower() or None,
                amount=str(edge.amount) if edge.amount is not None else None,
                provenance_ref=edge.provenance_ref,
                log_index=edge.log_index,
                vout=edge.vout,
            )
        return graph

    def analyze(
        self,
        investigation_id: str,
        nodes: list[GraphNodeInput],
        edges: list[GraphEdgeInput],
        evidence_transactions: list[TransactionRecord],
        verified_transactions: list[TransactionRecord] | None = None,
        require_node_membership: bool = True,
        require_provenance_ref: bool = False,
    ) -> tuple[GraphIntegritySummary, list[SecurityFinding]]:
        """Verify graph edges against evidence transactions; flag only concrete inconsistencies."""
        graph = self.build_networkx_graph(nodes, edges)

        declared_nodes: set[str] = set()
        for node in nodes:
            n_chain = normalize_chain_name(node.chain)
            declared_nodes.add(_norm_endpoint(node.node_id, n_chain))

        # Index evidence transactions as lists by (chain, tx_hash) and tx_hash to support
        # multi-edge UTXO transactions and multi-log ERC-20 transactions cleanly.
        ev_by_chain_hash: dict[tuple[str, str], list[TransactionRecord]] = {}
        ev_by_hash: dict[str, list[TransactionRecord]] = {}
        for tx in evidence_transactions:
            t_chain = normalize_chain_name(tx.chain)
            t_hash = _norm_tx_hash(tx.tx_hash)
            if t_hash:
                ev_by_chain_hash.setdefault((t_chain, t_hash), []).append(tx)
                ev_by_hash.setdefault(t_hash, []).append(tx)

        verified_by_chain_hash: dict[tuple[str, str], list[TransactionRecord]] = {}
        for vtx in verified_transactions or []:
            v_chain = normalize_chain_name(vtx.chain)
            v_hash = _norm_tx_hash(vtx.tx_hash)
            if v_hash:
                verified_by_chain_hash.setdefault((v_chain, v_hash), []).append(vtx)

        findings: list[SecurityFinding] = []
        seen_edge_signatures: dict[tuple[object, ...], str] = {}
        flagged_edges: set[str] = set()
        duplicate_edges = 0
        validated_edges = 0

        for edge in edges:
            e_chain = normalize_chain_name(edge.chain)
            e_hash = _norm_tx_hash(edge.tx_hash)
            e_src = _norm_endpoint(edge.source, e_chain)
            e_dst = _norm_endpoint(edge.target, e_chain)
            e_contract = (edge.token_contract or "").strip().lower()
            e_asset = (edge.asset or "").strip().upper()

            edge_issues: list[str] = []
            issue_category = FindingCategory.GRAPH_POISONING
            issue_type = "graph_edge_integrity_failure"
            severity = Severity.HIGH
            val_status = ValidationStatus.INVALID

            # 1. Duplicate relationship check
            dup_sig = (
                e_chain,
                e_src,
                e_dst,
                e_hash,
                edge.edge_type or "",
                e_contract or e_asset,
                edge.log_index,
                edge.vout,
            )
            if dup_sig in seen_edge_signatures:
                duplicate_edges += 1
                first_edge_id = seen_edge_signatures[dup_sig]
                edge_issues.append(
                    f"Duplicate graph edge matching existing edge '{first_edge_id}' for tx '{e_hash or 'none'}'"
                )
                issue_type = "duplicate_graph_edge"
                severity = Severity.MEDIUM
            else:
                seen_edge_signatures[dup_sig] = edge.edge_id

            # 2. Node reference existence check
            if require_node_membership and declared_nodes:
                if e_src not in declared_nodes:
                    edge_issues.append(
                        f"Source node '{edge.source}' is missing from declared graph nodes"
                    )
                if e_dst not in declared_nodes:
                    edge_issues.append(
                        f"Target node '{edge.target}' is missing from declared graph nodes"
                    )

            # 3. Supporting transaction reference check
            if not e_hash:
                edge_issues.append("Graph edge lacks a supporting transaction hash reference")
                issue_category = FindingCategory.DECOY_EDGE
                issue_type = "unsupported_graph_edge"
                val_status = ValidationStatus.INCOMPLETE
            else:
                candidates = ev_by_chain_hash.get((e_chain, e_hash), [])
                if not candidates:
                    other_chain_matches = ev_by_hash.get(e_hash, [])
                    if other_chain_matches:
                        actual_chains = sorted(
                            {normalize_chain_name(m.chain) for m in other_chain_matches}
                        )
                        edge_issues.append(
                            f"Chain identifier mismatch: edge declares '{e_chain or 'missing'}' while "
                            f"supporting transaction belongs to {actual_chains}"
                        )
                        issue_category = FindingCategory.DECOY_EDGE
                        issue_type = "graph_edge_chain_mismatch"
                    else:
                        edge_issues.append(
                            f"Missing supporting transaction evidence for tx_hash '{edge.tx_hash}' on chain '{e_chain}'"
                        )
                        issue_category = FindingCategory.DECOY_EDGE
                        issue_type = "missing_supporting_transaction"
                        val_status = ValidationStatus.UNVERIFIED
                elif edge.is_heuristic or (edge.edge_type or "").startswith("heuristic_"):
                    # Heuristic edges (e.g., Bitcoin co-spend) must never claim is_confirmed=True
                    # and both endpoints must belong to the supporting transaction's participants.
                    if edge.is_confirmed:
                        edge_issues.append(
                            "Heuristic edge improperly marked is_confirmed=True"
                        )
                    tx_participants = {
                        _norm_endpoint(addr, normalize_chain_name(tx.chain))
                        for tx in candidates
                        for addr in (tx.from_address or "", tx.to_address or "")
                        if addr
                    }
                    if tx_participants and (e_src not in tx_participants or e_dst not in tx_participants):
                        edge_issues.append(
                            f"Heuristic edge endpoints ({e_src}, {e_dst}) are not grounded in supporting tx '{edge.tx_hash}'"
                        )
                else:
                    evidence_tx = _select_matching_evidence(
                        edge, candidates, e_chain, e_src, e_dst, e_contract, e_asset
                    )
                    tx_chain = normalize_chain_name(evidence_tx.chain)
                    tx_src = _norm_endpoint(evidence_tx.from_address or "", tx_chain)
                    tx_dst = _norm_endpoint(evidence_tx.to_address or "", tx_chain)

                    if e_chain != tx_chain:
                        edge_issues.append(
                            f"Chain mismatch: edge='{e_chain}' vs evidence='{tx_chain}'"
                        )
                    if tx_src and e_src != tx_src:
                        if e_src == tx_dst and e_dst == tx_src:
                            edge_issues.append(
                                "Transfer direction contradiction: edge source/target are reversed relative to transaction evidence"
                            )
                            issue_category = FindingCategory.DECOY_EDGE
                        else:
                            edge_issues.append(
                                f"Source address inconsistency: edge='{e_src}' vs evidence='{tx_src}'"
                            )
                    if tx_dst and e_dst != tx_dst:
                        edge_issues.append(
                            f"Destination address inconsistency: edge='{e_dst}' vs evidence='{tx_dst}'"
                        )
                    if (
                        edge.block_number is not None
                        and evidence_tx.block_number is not None
                        and edge.block_number != evidence_tx.block_number
                    ):
                        edge_issues.append(
                            f"Block reference mismatch: edge={edge.block_number} vs evidence={evidence_tx.block_number}"
                        )
                    if (
                        e_asset
                        and evidence_tx.asset_symbol
                        and e_asset != evidence_tx.asset_symbol.strip().upper()
                    ):
                        edge_issues.append(
                            f"Asset symbol mismatch: edge='{e_asset}' vs evidence='{evidence_tx.asset_symbol}'"
                        )
                    if (
                        e_contract
                        and evidence_tx.token_contract
                        and e_contract != evidence_tx.token_contract.strip().lower()
                    ):
                        edge_issues.append(
                            f"Token contract mismatch: edge='{e_contract}' vs evidence='{evidence_tx.token_contract.lower()}'"
                        )
                    edge_amt = _to_decimal(edge.amount)
                    tx_amt = _to_decimal(evidence_tx.amount)
                    if edge_amt is not None and tx_amt is not None and edge_amt != tx_amt:
                        edge_issues.append(f"Amount mismatch: edge={edge_amt} vs evidence={tx_amt}")
                    if require_provenance_ref and not (
                        edge.provenance_ref or evidence_tx.provenance_id
                    ):
                        edge_issues.append(
                            "Missing provenance reference on edge and supporting transaction"
                        )
                        val_status = ValidationStatus.INCOMPLETE
                    elif (
                        edge.provenance_ref
                        and evidence_tx.provenance_id
                        and edge.provenance_ref != evidence_tx.provenance_id
                    ):
                        edge_issues.append(
                            f"Provenance reference conflict: edge='{edge.provenance_ref}' vs evidence='{evidence_tx.provenance_id}'"
                        )

                    verified_candidates = verified_by_chain_hash.get((e_chain, e_hash), [])
                    if verified_candidates:
                        verified_tx = _select_matching_evidence(
                            edge, verified_candidates, e_chain, e_src, e_dst, e_contract, e_asset
                        )
                        v_src = _norm_endpoint(verified_tx.from_address or "", e_chain)
                        v_dst = _norm_endpoint(verified_tx.to_address or "", e_chain)
                        v_amt = _to_decimal(verified_tx.amount)
                        if v_src and e_src != v_src:
                            edge_issues.append(
                                f"Contradiction with verified chain record (source): edge='{e_src}' vs verified='{v_src}'"
                            )
                            val_status = ValidationStatus.CONFLICTING
                        if v_dst and e_dst != v_dst:
                            edge_issues.append(
                                f"Contradiction with verified chain record (target): edge='{e_dst}' vs verified='{v_dst}'"
                            )
                            val_status = ValidationStatus.CONFLICTING
                        if (
                            verified_tx.block_number is not None
                            and edge.block_number is not None
                            and edge.block_number != verified_tx.block_number
                        ):
                            edge_issues.append(
                                f"Contradiction with verified chain record (block): edge={edge.block_number} vs verified={verified_tx.block_number}"
                            )
                            val_status = ValidationStatus.CONFLICTING
                        if v_amt is not None and edge_amt is not None and v_amt != edge_amt:
                            edge_issues.append(
                                f"Contradiction with verified chain record (amount): edge={edge_amt} vs verified={v_amt}"
                            )
                            val_status = ValidationStatus.CONFLICTING

            if edge_issues:
                flagged_edges.add(edge.edge_id)
                ev_refs = [
                    EvidenceReference(
                        ref_type="graph_edge",
                        ref_id=edge.edge_id,
                        chain=e_chain or None,
                        detail=f"{e_src} -> {e_dst}",
                    )
                ]
                if edge.tx_hash:
                    ev_refs.append(
                        EvidenceReference(
                            ref_type="transaction",
                            ref_id=edge.tx_hash,
                            chain=e_chain or None,
                        )
                    )

                findings.append(
                    SecurityFinding(
                        investigation_id=investigation_id,
                        finding_category=issue_category,
                        finding_type=issue_type,
                        severity=severity,
                        confidence=0.92
                        if val_status in (ValidationStatus.INVALID, ValidationStatus.CONFLICTING)
                        else 0.78,
                        epistemic_label=EpistemicLabel.VERIFIED_FACT
                        if val_status == ValidationStatus.CONFLICTING
                        else EpistemicLabel.SUSPICIOUS_INDICATOR,
                        description=(
                            f"Graph integrity failure on edge '{edge.edge_id}' ({edge.source} -> {edge.target})."
                        ),
                        source_address=e_src,
                        suspected_lookalike_address=None,
                        evidence_references=ev_refs,
                        supporting_transaction_refs=[edge.tx_hash] if edge.tx_hash else [],
                        detection_source="graph_integrity_analyzer",
                        validation_status=val_status,
                        explanation="; ".join(edge_issues) + ".",
                        limitations=[
                            "Graph integrity verification checks edge consistency against supplied transaction evidence; omitted external transactions cannot be verified without full chain indexing."
                        ],
                        recommended_action=(
                            "Quarantine or rebuild affected graph edges from verified raw transaction receipts before relying on graph rankings."
                        ),
                        metadata={
                            "edge_id": edge.edge_id,
                            "issues": edge_issues,
                            "chain": e_chain,
                        },
                    )
                )
            else:
                validated_edges += 1

        summary = GraphIntegritySummary(
            node_count=graph.number_of_nodes(),
            edge_count=graph.number_of_edges(),
            validated_edge_count=validated_edges,
            flagged_edge_count=len(flagged_edges),
            duplicate_edge_count=duplicate_edges,
            is_integrity_clean=len(findings) == 0,
        )
        return summary, findings

