"""Cross-case relationship analysis across multiple investigation graphs."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Set, Tuple

from forensics.config import CrossCaseConfig
from forensics.detectors.base import FindingIdSequence, clamp, make_finding
from forensics.graph.index import InvestigationGraphIndex
from forensics.schemas.input import InvestigationCase
from forensics.schemas.output import CrossCaseAnalysisResponse, CrossCaseFinding


def analyze_cross_case_relationships(
    cases: List[InvestigationCase],
    cfg: CrossCaseConfig,
    indices: Dict[str, InvestigationGraphIndex] | None = None,
) -> CrossCaseAnalysisResponse:
    """Compare multiple investigation graphs to detect shared infrastructure and path overlap."""
    if indices is None:
        indices = {case.investigation_id: InvestigationGraphIndex(case) for case in cases}

    seq = FindingIdSequence(prefix="CC", start=1)
    benign_cats = {c.lower() for c in cfg.exclude_benign_public_hub_categories}

    addr_to_cases: Dict[str, Set[str]] = defaultdict(set)
    sink_to_cases: Dict[str, Set[str]] = defaultdict(set)
    edge_to_cases: Dict[Tuple[str, str], Set[str]] = defaultdict(set)
    ignored_hubs: Set[str] = set()

    for case in cases:
        cid = case.investigation_id
        idx = indices[cid]
        for addr in idx.all_addresses:
            if idx.has_category(addr, benign_cats):
                ignored_hubs.add(addr)
                continue
            addr_to_cases[addr].add(cid)
            if idx.nx_graph.out_degree(addr) == 0 and idx.nx_graph.in_degree(addr) > 0:
                sink_to_cases[addr].add(cid)

        for u, v in idx.nx_graph.edges():
            if idx.has_category(u, benign_cats) or idx.has_category(v, benign_cats):
                continue
            edge_to_cases[(u, v)].add(cid)

    findings: List[CrossCaseFinding] = []

    # 1. Common downstream destinations (non-public-hub sinks shared across >= min_shared_cases)
    for sink, case_ids in sorted(sink_to_cases.items()):
        if len(case_ids) < cfg.min_shared_cases:
            continue
        sorted_cids = sorted(case_ids)
        ev_refs: List[str] = []
        for cid in sorted_cids:
            ev_refs.extend(leg.tx_id for leg in indices[cid].inbound_legs.get(sink, []))
        if not ev_refs:
            # Fallback to edge IDs when normalized txs aren't present
            for cid in sorted_cids:
                for u, _, data in indices[cid].nx_graph.in_edges(sink, data=True):
                    ev_refs.append(str(data.get("edge_id", f"{u}->{sink}")))

        finding = make_finding(
            seq,
            rule_id="CROSS-CASE-DEST-01",
            rule_version=cfg.rule_version,
            title="Common downstream destination across investigations",
            category="cross_case_intelligence",
            severity="high",
            confidence=clamp(0.72 + 0.06 * (len(sorted_cids) - 2), 0.72, 0.90),
            explanation=(
                f"Unlabelled/non-public destination {sink} appears as a terminal sink in "
                f"{len(sorted_cids)} separate investigations ({', '.join(sorted_cids)})."
            ),
            evidence_refs=ev_refs,
            limitations=[
                "Shared destination address may represent an unlabelled third-party service, OTC broker, or shared infrastructure rather than the same ultimate owner."
            ],
            affected_addresses=[sink],
            relationship_status="confirmed",
            metadata={"case_ids": sorted_cids},
        )
        findings.append(
            CrossCaseFinding(
                finding=finding,
                case_ids=sorted_cids,
                shared_addresses=[sink],
                common_destinations=[sink],
            )
        )

    # 2. Overlapping suspicious transaction paths (shared multi-hop edges)
    shared_edges_by_pair_cases: Dict[Tuple[str, ...], List[Tuple[str, str]]] = defaultdict(list)
    for (u, v), case_ids in sorted(edge_to_cases.items()):
        if len(case_ids) >= cfg.min_shared_cases:
            shared_edges_by_pair_cases[tuple(sorted(case_ids))].append((u, v))

    for case_tuple, edges in sorted(shared_edges_by_pair_cases.items()):
        # Reconstruct connected overlapping paths
        adj: Dict[str, List[str]] = defaultdict(list)
        nodes_in_edges: Set[str] = set()
        for u, v in edges:
            adj[u].append(v)
            nodes_in_edges.add(u)
            nodes_in_edges.add(v)

        paths: List[List[str]] = []
        for start in sorted(nodes_in_edges):
            for nxt in adj.get(start, []):
                path = [start, nxt]
                curr = nxt
                while adj.get(curr):
                    cand = adj[curr][0]
                    if cand in path:
                        break
                    path.append(cand)
                    curr = cand
                if len(path) >= cfg.min_overlapping_path_length:
                    paths.append(path)

        if paths:
            longest = max(paths, key=len)
            ev_refs = []
            for cid in case_tuple:
                idx = indices[cid]
                for i in range(len(longest) - 1):
                    data = idx.nx_graph.get_edge_data(longest[i], longest[i + 1]) or {}
                    ev_refs.extend(data.get("tx_ids", []))

            finding = make_finding(
                seq,
                rule_id="CROSS-CASE-PATH-01",
                rule_version=cfg.rule_version,
                title="Overlapping transaction path across investigations",
                category="cross_case_intelligence",
                severity="high",
                confidence=clamp(0.70 + 0.05 * len(longest), 0.70, 0.90),
                explanation=(
                    f"Investigations {', '.join(case_tuple)} share overlapping transaction path "
                    f"{' -> '.join(longest)}."
                ),
                evidence_refs=ev_refs,
                limitations=[
                    "Overlapping infrastructure may reflect shared intermediary relays or unlabelled services."
                ],
                affected_addresses=longest,
                relationship_status="confirmed",
                metadata={"case_ids": list(case_tuple), "overlapping_path": longest},
            )
            findings.append(
                CrossCaseFinding(
                    finding=finding,
                    case_ids=list(case_tuple),
                    shared_addresses=longest,
                    overlapping_paths=[longest],
                )
            )

    # 3. Shared intermediary / non-sink wallet nodes not already reported as common destinations
    reported_sinks = set(sink_to_cases.keys())
    for addr, case_ids in sorted(addr_to_cases.items()):
        if addr in reported_sinks or len(case_ids) < cfg.min_shared_cases:
            continue
        sorted_cids = sorted(case_ids)
        ev_refs = []
        for cid in sorted_cids:
            idx = indices[cid]
            ev_refs.extend(leg.tx_id for leg in idx.inbound_legs.get(addr, []))
            ev_refs.extend(leg.tx_id for leg in idx.outbound_legs.get(addr, []))
        if not ev_refs:
            continue
        finding = make_finding(
            seq,
            rule_id="CROSS-CASE-NODE-01",
            rule_version=cfg.rule_version,
            title="Shared intermediary wallet across investigations",
            category="cross_case_intelligence",
            severity="medium",
            confidence=0.68,
            explanation=(
                f"Address {addr} appears across {len(sorted_cids)} investigations "
                f"({', '.join(sorted_cids)}) with supporting transaction evidence."
            ),
            evidence_refs=ev_refs,
            limitations=[
                "Shared intermediary nodes can be unlabelled liquidity providers, OTC desks, or relayers."
            ],
            affected_addresses=[addr],
            relationship_status="confirmed",
            metadata={"case_ids": sorted_cids},
        )
        findings.append(
            CrossCaseFinding(
                finding=finding,
                case_ids=sorted_cids,
                shared_addresses=[addr],
            )
        )

    return CrossCaseAnalysisResponse(
        analyzed_case_ids=[c.investigation_id for c in cases],
        cross_case_findings=findings,
        ignored_public_hubs=sorted(ignored_hubs),
    )
