"""Address and wallet clustering detector with CoinJoin & collaborative tx safeguards."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Dict, List, Set, Tuple

from forensics.config import ClusteringConfig
from forensics.detectors.base import FindingIdSequence, clamp, make_finding
from forensics.graph.index import InvestigationGraphIndex
from forensics.schemas.input import NormalizedTransaction
from forensics.schemas.output import ClusterEdgeReason, ClusterGroup, ForensicFinding


BENIGN_SHARED_SERVICE_CATEGORIES = {
    "exchange",
    "cex",
    "merchant",
    "payment_processor",
    "defi_router",
    "bridge",
    "payroll",
    "mixer",
}


class _UnionFind:
    def __init__(self) -> None:
        self.parent: Dict[str, str] = {}

    def find(self, x: str) -> str:
        if x not in self.parent:
            self.parent[x] = x
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            if ra < rb:
                self.parent[rb] = ra
            else:
                self.parent[ra] = rb


def is_suspected_collaborative_tx(
    tx: NormalizedTransaction, cfg: ClusteringConfig
) -> Tuple[bool, str]:
    """Detect CoinJoin, PayJoin, or collaborative UTXO transactions to avoid CIOH false positives."""
    if tx.is_collaborative_hint is True:
        return True, "Upstream collaborative transaction hint set."
    if tx.metadata.get("is_payjoin") or tx.metadata.get("is_coinjoin"):
        return True, "Transaction metadata indicates collaborative CoinJoin/PayJoin structure."

    if not tx.inputs or not tx.outputs:
        return False, ""

    distinct_inputs = {inp.address for inp in tx.inputs}
    if len(distinct_inputs) < cfg.coinjoin_min_inputs:
        return False, ""

    # Check for >= N equal-value outputs sent to distinct output addresses (classic CoinJoin signature)
    out_values = [(out.address, out.value) for out in tx.outputs if out.value > 0]
    for _, anchor_val in out_values:
        matching_addrs = {
            addr
            for addr, val in out_values
            if abs(val - anchor_val) <= max(1e-9, anchor_val * cfg.coinjoin_value_tolerance)
        }
        if len(matching_addrs) >= cfg.coinjoin_min_equal_outputs:
            return (
                True,
                f"Detected {len(matching_addrs)} distinct equal-value outputs (~{anchor_val:.6g}) "
                f"with {len(distinct_inputs)} distinct input addresses (likely CoinJoin).",
            )

    return False, ""


def detect_wallet_clusters(
    index: InvestigationGraphIndex,
    cfg: ClusteringConfig,
    seq: FindingIdSequence,
) -> Tuple[List[ClusterGroup], List[ForensicFinding]]:
    """Run conservative wallet clustering heuristics and emit explainable findings."""
    uf = _UnionFind()
    edge_reasons: List[ClusterEdgeReason] = []
    suppressed_coinjoin_txs: List[str] = []
    coinjoin_notes: List[str] = []
    findings: List[ForensicFinding] = []

    def _can_link(addr_a: str, addr_b: str) -> bool:
        if addr_a == addr_b:
            return False
        lbl_a = index.get_primary_label(addr_a)
        lbl_b = index.get_primary_label(addr_b)
        # Never merge two distinct verified entities (e.g., two different exchanges or services)
        if lbl_a and lbl_b and lbl_a.verified and lbl_b.verified and lbl_a.label != lbl_b.label:
            return False
        if index.has_category(addr_a, BENIGN_SHARED_SERVICE_CATEGORIES) or index.has_category(
            addr_b, BENIGN_SHARED_SERVICE_CATEGORIES
        ):
            return False
        return True

    # 1. UTXO Common-Input Ownership Heuristic (CIOH) + Address Reuse (with CoinJoin guard)
    reused_addresses: Dict[str, List[str]] = defaultdict(list)

    for tx in index.case.transactions:
        if not (tx.inputs or tx.outputs):
            continue

        is_collab, collab_reason = is_suspected_collaborative_tx(tx, cfg)
        if is_collab:
            suppressed_coinjoin_txs.append(tx.tx_id)
            coinjoin_notes.append(f"{tx.tx_id}: {collab_reason}")
            continue

        distinct_inputs = sorted({inp.address for inp in tx.inputs})
        if len(distinct_inputs) >= 2:
            # Confidence decreases slightly when many inputs exist without corroboration
            cioh_conf = clamp(
                cfg.max_cioh_confidence - 0.02 * max(0, len(distinct_inputs) - 3),
                0.45,
                cfg.max_cioh_confidence,
            )
            anchor = distinct_inputs[0]
            for other in distinct_inputs[1:]:
                if _can_link(anchor, other):
                    uf.union(anchor, other)
                    edge_reasons.append(
                        ClusterEdgeReason(
                            address_a=anchor,
                            address_b=other,
                            heuristic="common_input_ownership",
                            confidence=round(cioh_conf, 4),
                            relationship_status="inferred",
                            reason=(
                                f"Co-spent in non-collaborative UTXO transaction {tx.tx_id} "
                                f"({len(distinct_inputs)} distinct inputs)."
                            ),
                            evidence_refs=[tx.tx_id],
                            counter_evidence=[
                                "Multi-input spending can occur in PayJoin, custodial batching, or collaborative wallets."
                            ],
                        )
                    )

        # Address reuse: an input address also receives an output (self-change reuse)
        input_set = set(distinct_inputs)
        output_set = {out.address for out in tx.outputs}
        for reused in sorted(input_set & output_set):
            reused_addresses[reused].append(tx.tx_id)

    # 2. Repeated Counterparty Heuristic (for non-service addresses)
    pair_txs: Dict[Tuple[str, str], List[str]] = defaultdict(list)
    for addr, legs in index.outbound_legs.items():
        for leg in legs:
            pair = (min(leg.sender, leg.receiver), max(leg.sender, leg.receiver))
            pair_txs[pair].append(leg.tx_id)

    for (addr_a, addr_b), tx_ids in sorted(pair_txs.items()):
        unique_tx_ids = sorted(set(tx_ids))
        if len(unique_tx_ids) >= cfg.repeated_counterparty_min_txs and _can_link(addr_a, addr_b):
            # Only treat repeated bilateral transfers as weak behavioural clustering if bidirectional
            a_to_b = any(
                leg.sender == addr_a and leg.receiver == addr_b
                for leg in index.outbound_legs.get(addr_a, [])
            )
            b_to_a = any(
                leg.sender == addr_b and leg.receiver == addr_a
                for leg in index.outbound_legs.get(addr_b, [])
            )
            if a_to_b and b_to_a:
                uf.union(addr_a, addr_b)
                edge_reasons.append(
                    ClusterEdgeReason(
                        address_a=addr_a,
                        address_b=addr_b,
                        heuristic="repeated_bidirectional_counterparty",
                        confidence=0.58,
                        relationship_status="inferred",
                        reason=(
                            f"Observed {len(unique_tx_ids)} bidirectional transfers between addresses "
                            "without service labels."
                        ),
                        evidence_refs=unique_tx_ids,
                        counter_evidence=[
                            "Repeated transfers may reflect OTC trading, recurring commercial settlement, or two cooperating parties."
                        ],
                    )
                )

    # 3. Synchronized Outbound Timing Heuristic
    outbound_events: List[Tuple[float, str, str]] = []
    for addr, legs in index.outbound_legs.items():
        if index.has_category(addr, BENIGN_SHARED_SERVICE_CATEGORIES):
            continue
        for leg in legs:
            outbound_events.append((leg.timestamp.timestamp(), addr, leg.tx_id))
    outbound_events.sort(key=lambda item: item[0])

    sync_pairs: Dict[Tuple[str, str], List[str]] = defaultdict(list)
    for i, (ts_i, addr_i, tx_i) in enumerate(outbound_events):
        j = i + 1
        while j < len(outbound_events) and (outbound_events[j][0] - ts_i) <= cfg.timing_window_seconds:
            _, addr_j, tx_j = outbound_events[j]
            if addr_i != addr_j and _can_link(addr_i, addr_j):
                pair = (min(addr_i, addr_j), max(addr_i, addr_j))
                sync_pairs[pair].extend([tx_i, tx_j])
            j += 1

    for (addr_a, addr_b), tx_refs in sorted(sync_pairs.items()):
        unique_refs = sorted(set(tx_refs))
        # Divide by 2 since each pair contributes 2 tx_ids per event
        if len(unique_refs) >= cfg.min_timing_pair_count * 2:
            uf.union(addr_a, addr_b)
            edge_reasons.append(
                ClusterEdgeReason(
                    address_a=addr_a,
                    address_b=addr_b,
                    heuristic="synchronized_transaction_timing",
                    confidence=0.54,
                    relationship_status="inferred",
                    reason=(
                        f"Both addresses initiated outbound transactions within {cfg.timing_window_seconds}s "
                        f"across multiple intervals ({len(unique_refs)} transactions)."
                    ),
                    evidence_refs=unique_refs,
                    counter_evidence=[
                        "Synchronized timing can be caused by shared block-time batching, market events, or automated bots owned by different users."
                    ],
                )
            )

    # Build ClusterGroup objects
    grouped: Dict[str, Set[str]] = defaultdict(set)
    for reason in edge_reasons:
        root = uf.find(reason.address_a)
        grouped[root].add(reason.address_a)
        grouped[root].add(reason.address_b)

    clusters: List[ClusterGroup] = []
    for idx, (_, members) in enumerate(sorted(grouped.items()), start=1):
        member_list = sorted(members)
        reasons_for_group = [
            r for r in edge_reasons if r.address_a in members and r.address_b in members
        ]
        # Combine multi-heuristic support conservatively, capped below 1.0
        heuristics_used = Counter(r.heuristic for r in reasons_for_group)
        max_single = max((r.confidence for r in reasons_for_group), default=0.5)
        bonus = 0.05 * max(0, len(heuristics_used) - 1)
        group_conf = clamp(max_single + bonus, 0.0, cfg.cluster_confidence_cap)
        all_refs = sorted({ref for r in reasons_for_group for ref in r.evidence_refs})

        limitations = [
            "Wallet clustering is probabilistic/inferred and never proves single human ownership.",
            "Collaborative spending, custodial wallets, or shared automation can produce false cluster edges.",
        ]
        if suppressed_coinjoin_txs:
            limitations.append(
                f"Suppressed CIOH on {len(suppressed_coinjoin_txs)} suspected collaborative/CoinJoin tx(s)."
            )

        cluster = ClusterGroup(
            cluster_id=f"CL-{idx:04d}",
            addresses=member_list,
            confidence=round(group_conf, 4),
            reasons=reasons_for_group,
            suppressed_coinjoin_txs=sorted(set(suppressed_coinjoin_txs)),
            limitations=limitations,
        )
        clusters.append(cluster)

        findings.append(
            make_finding(
                seq,
                rule_id="CLUSTER-HEURISTIC-01",
                rule_version=cfg.rule_version,
                title=f"Inferred wallet cluster ({len(member_list)} addresses)",
                category="wallet_clustering",
                severity="medium",
                confidence=group_conf,
                explanation=(
                    f"Grouped {len(member_list)} addresses into candidate cluster {cluster.cluster_id} "
                    f"using heuristics: {', '.join(sorted(heuristics_used.keys()))}."
                ),
                evidence_refs=all_refs,
                limitations=limitations,
                affected_addresses=member_list,
                relationship_status="inferred",
                metadata={
                    "cluster_id": cluster.cluster_id,
                    "heuristics": dict(heuristics_used),
                },
            )
        )

    # Emit address reuse findings
    for addr, tx_ids in sorted(reused_addresses.items()):
        if len(set(tx_ids)) >= 1:
            findings.append(
                make_finding(
                    seq,
                    rule_id="CLUSTER-ADDR-REUSE-01",
                    rule_version=cfg.rule_version,
                    title="UTXO address reuse detected",
                    category="wallet_clustering",
                    severity="low",
                    confidence=0.78,
                    explanation=(
                        f"Address {addr} appeared in both inputs and outputs across {len(set(tx_ids))} "
                        "UTXO transaction(s), weakening privacy and revealing likely change continuity."
                    ),
                    evidence_refs=sorted(set(tx_ids)),
                    limitations=[
                        "Address reuse indicates wallet software behaviour or consolidation, not necessarily illicit intent."
                    ],
                    affected_addresses=[addr],
                    relationship_status="confirmed",
                )
            )

    # Emit explicit CoinJoin / collaborative CIOH suppression finding so safeguards are auditable
    if suppressed_coinjoin_txs:
        findings.append(
            make_finding(
                seq,
                rule_id="CLUSTER-COINJOIN-GUARD-01",
                rule_version=cfg.rule_version,
                title="Common-input clustering suppressed on collaborative transaction(s)",
                category="clustering_safeguard",
                severity="low",
                confidence=0.90,
                explanation=(
                    f"Suppressed common-input ownership clustering on {len(set(suppressed_coinjoin_txs))} "
                    "transaction(s) exhibiting CoinJoin/collaborative equal-output structure: "
                    + "; ".join(coinjoin_notes[:3])
                ),
                evidence_refs=sorted(set(suppressed_coinjoin_txs)),
                limitations=[
                    "Collaborative transactions combine inputs from unrelated participants; merging inputs would cause severe false attribution."
                ],
                affected_addresses=[],
                relationship_status="confirmed",
                metadata={"suppressed_tx_ids": sorted(set(suppressed_coinjoin_txs))},
            )
        )

    return clusters, findings
