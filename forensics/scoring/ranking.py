"""Probable end-receiver ranking algorithm (candidate destinations, never human identity)."""

from __future__ import annotations

from typing import Dict, List, Set

from forensics.config import ReceiverRankingConfig
from forensics.detectors.base import clamp
from forensics.features.extractor import extract_wallet_features
from forensics.graph.index import InvestigationGraphIndex
from forensics.schemas.output import ForensicFinding, ReceiverCandidate


def rank_probable_end_receivers(
    index: InvestigationGraphIndex,
    findings: List[ForensicFinding],
    cfg: ReceiverRankingConfig,
    coverage_score: float,
) -> List[ReceiverCandidate]:
    """Rank candidate end-receiver destinations using path, value, provenance, and counter-evidence."""
    paths = index.shortest_paths_from_seeds()
    seeds = set(index.case.seed_addresses)
    if not paths:
        return []

    # Candidate destinations: reachable non-seed addresses that received value
    # Prioritize terminal sinks (out_degree == 0) and high-retention endpoints
    total_traced_inflow = sum(
        extract_wallet_features(index, addr).total_inflow
        for addr in paths
        if addr not in seeds
    )
    max_sink_inflow = max(
        (
            extract_wallet_features(index, addr).total_inflow
            for addr in paths
            if addr not in seeds
        ),
        default=1.0,
    )
    max_sink_inflow = max(max_sink_inflow, 1e-9)

    findings_by_addr: Dict[str, List[ForensicFinding]] = {}
    for f in findings:
        for addr in f.affected_addresses:
            findings_by_addr.setdefault(addr, []).append(f)

    # Identify downstream candidates (exclude seeds unless no non-seed exists)
    candidate_addrs = [addr for addr in paths.keys() if addr not in seeds]
    if not candidate_addrs:
        return []

    w = cfg.weights
    candidates: List[ReceiverCandidate] = []
    sink_count = sum(1 for addr in candidate_addrs if index.nx_graph.out_degree(addr) == 0)

    for addr in candidate_addrs:
        path = paths[addr]
        hop_dist = max(0, len(path) - 1)
        feat = extract_wallet_features(index, addr)
        if feat.total_inflow <= 0 and index.nx_graph.in_degree(addr) == 0:
            continue

        is_terminal_sink = index.nx_graph.out_degree(addr) == 0
        # 1. Trace-path position: terminal sinks & deeper peel endpoints rank higher than transient hops
        if is_terminal_sink:
            trace_pos = 1.0
        else:
            trace_pos = clamp(0.35 + 0.40 * feat.residual_balance_ratio, 0.1, 0.85)

        # 2. Value proportion relative to strongest candidate / traced seed outflow
        seed_outflow = sum(
            extract_wallet_features(index, s).total_outflow for s in seeds if s in index.all_addresses
        )
        denom = seed_outflow if seed_outflow > 0 else max_sink_inflow
        value_prop = clamp(feat.total_inflow / max(denom, 1e-9), 0.0, 1.0)

        # 3. Path consistency: confirmed edges along shortest path
        edge_confs: List[float] = []
        inferred_hops = 0
        for i in range(len(path) - 1):
            edata = index.nx_graph.get_edge_data(path[i], path[i + 1]) or {}
            status = edata.get("relationship_status", "confirmed")
            econf = float(edata.get("confidence", 1.0 if status == "confirmed" else 0.65))
            if status == "inferred":
                inferred_hops += 1
                econf = min(econf, 0.72)
            edge_confs.append(econf)
        path_consistency = (
            sum(edge_confs) / len(edge_confs) if edge_confs else 0.5
        )

        # 4. Supporting findings on candidate or along its path
        path_findings: List[ForensicFinding] = []
        seen_fids: Set[str] = set()
        for node_addr in path:
            for f in findings_by_addr.get(node_addr, []):
                if f.finding_id not in seen_fids and f.category != "clustering_safeguard":
                    seen_fids.add(f.finding_id)
                    path_findings.append(f)

        support_score = clamp(
            sum(f.confidence for f in path_findings) / max(1.0, len(path_findings) + 0.5)
            if path_findings
            else 0.0
        )

        # 5. Label provenance & known-service exposure
        primary_lbl = index.get_primary_label(addr)
        if primary_lbl is not None:
            label_prov_score = 1.0 if primary_lbl.verified else 0.6
            label_text = primary_lbl.label
            prov_text = f"{primary_lbl.provenance} ({'verified' if primary_lbl.verified else 'unverified'})"
        else:
            label_prov_score = 0.25
            label_text = None
            prov_text = "unlabelled"

        # 6. Local observation coverage for candidate
        node = index.node_by_address.get(addr)
        local_cov = coverage_score
        if node and not node.observed_in_full:
            local_cov *= 0.65
        if node and node.missing_neighbors_estimated > 0:
            local_cov *= 0.80
        local_cov = clamp(local_cov)

        # Counter-evidence collection
        counter_evidence: List[str] = []
        if inferred_hops > 0:
            counter_evidence.append(
                f"Path includes {inferred_hops} inferred relationship hop(s), reducing attribution certainty."
            )
        if not is_terminal_sink and feat.residual_balance_ratio < 0.15:
            counter_evidence.append(
                "Candidate forwarded most funds onward (low residual balance); may be an intermediary rather than final destination."
            )
        if sink_count > 2 and is_terminal_sink:
            counter_evidence.append(
                f"Multiple competing terminal destinations ({sink_count}) observed in trace graph."
            )
        if index.has_category(addr, {"mixer"}):
            counter_evidence.append(
                "Destination is a mixer pool; onward post-mix recipients are unlinked or obscured."
            )
        if index.has_category(addr, {"exchange", "cex"}):
            counter_evidence.append(
                "Destination is a labelled exchange service; funds may enter custodial omnibus pooling."
            )
        if node and not node.observed_in_full:
            counter_evidence.append("Candidate node history was not observed in full.")

        ranking_score = clamp(
            w.get("trace_position", 0.20) * trace_pos
            + w.get("value_proportion", 0.25) * value_prop
            + w.get("path_consistency", 0.20) * path_consistency
            + w.get("supporting_findings", 0.15) * support_score
            + w.get("label_provenance", 0.10) * label_prov_score
            + w.get("investigation_coverage", 0.10) * local_cov
        )

        # Separate risk_priority vs attribution_confidence per candidate
        max_finding_sev = max(
            ({"low": 0.25, "medium": 0.55, "high": 0.80, "critical": 0.95}[f.severity] for f in path_findings),
            default=0.1,
        )
        cand_risk = clamp(0.55 * max_finding_sev + 0.45 * feat.known_risk_service_exposure)
        if primary_lbl and primary_lbl.risk_indicator in {"high", "critical"}:
            cand_risk = max(cand_risk, 0.78 if primary_lbl.risk_indicator == "high" else 0.92)
        if index.has_category(addr, {"mixer"}) and not (
            primary_lbl and primary_lbl.risk_indicator in {"high", "critical"}
        ):
            # Never equate mixer exposure with criminality
            cand_risk = min(cand_risk, 0.55)

        cand_attr_conf = clamp(
            0.45 * path_consistency + 0.30 * local_cov + 0.25 * label_prov_score
        )
        if inferred_hops > 0:
            cand_attr_conf = min(cand_attr_conf, 0.78)

        limitations = [
            "Candidate destination reflects observed on-chain flow only and does NOT identify a real-world human owner.",
            "Off-chain settlement, internal exchange accounting, or unexpanded downstream hops are not observable.",
        ]

        candidates.append(
            ReceiverCandidate(
                rank=0,
                candidate_destination=addr,
                entity_label=label_text,
                label_provenance=prov_text,
                trace_path=path,
                hop_distance=hop_dist,
                value_received=round(feat.total_inflow, 8),
                value_proportion=round(value_prop, 4),
                ranking_score=round(ranking_score, 4),
                risk_priority=round(cand_risk, 4),
                attribution_confidence=round(cand_attr_conf, 4),
                path_consistency=round(path_consistency, 4),
                investigation_coverage=round(local_cov, 4),
                supporting_finding_ids=[f.finding_id for f in path_findings],
                counter_evidence=counter_evidence,
                limitations=limitations,
            )
        )

    candidates.sort(
        key=lambda c: (c.ranking_score, c.value_proportion, c.attribution_confidence),
        reverse=True,
    )
    for idx, cand in enumerate(candidates, start=1):
        cand.rank = idx

    return candidates
