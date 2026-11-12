"""Peel-chain forwarding detector for UTXO and account-based chains."""

from __future__ import annotations

from typing import Dict, List, Set, Tuple

from forensics.config import PeelChainConfig
from forensics.detectors.base import FindingIdSequence, clamp, make_finding
from forensics.graph.index import InvestigationGraphIndex, TransferLeg
from forensics.schemas.output import ForensicFinding


EXCLUDED_PEEL_INTERMEDIARY_CATEGORIES = {
    "exchange",
    "cex",
    "defi_router",
    "bridge",
    "payroll",
    "merchant",
    "payment_processor",
}


def _min_value_for_chain(chain: str, cfg: PeelChainConfig) -> float:
    return cfg.min_hop_value_btc if chain == "bitcoin" else cfg.min_hop_value_eth


def detect_peel_chains(
    index: InvestigationGraphIndex,
    cfg: PeelChainConfig,
    seq: FindingIdSequence,
) -> List[ForensicFinding]:
    """Detect repeated sequential forwarding with value peeling and residual balances."""
    min_val = _min_value_for_chain(index.chain, cfg)
    findings: List[ForensicFinding] = []

    # Build hop transitions: from an inbound leg at node u, find valid continuation leg (u -> v)
    # where outgoing continuation value is within [min_continuation_ratio, max_continuation_ratio]
    # of received value (or tx total input in UTXO split).
    visited_chains: Set[Tuple[str, ...]] = set()

    def _find_next_hops(
        current_addr: str, received_val: float, prev_ts_sec: float
    ) -> List[Tuple[TransferLeg, float, float]]:
        if index.has_category(current_addr, EXCLUDED_PEEL_INTERMEDIARY_CATEGORIES):
            return []

        candidates: List[Tuple[TransferLeg, float, float]] = []
        for out_leg in index.outbound_legs.get(current_addr, []):
            dt = out_leg.timestamp.timestamp() - prev_ts_sec
            if dt < 0 or dt > cfg.max_hop_delay_seconds:
                continue
            if out_leg.value < min_val or received_val <= 0:
                continue

            ratio = out_leg.value / received_val
            if cfg.min_continuation_ratio <= ratio <= cfg.max_continuation_ratio:
                residual = max(0.0, received_val - out_leg.value)
                candidates.append((out_leg, ratio, residual))
        return candidates

    # Candidate starting points sorted chronologically (earliest root transfers first)
    start_legs: List[TransferLeg] = []
    for addr in sorted(index.all_addresses):
        if index.has_category(addr, EXCLUDED_PEEL_INTERMEDIARY_CATEGORIES):
            continue
        for leg in index.outbound_legs.get(addr, []):
            if leg.value >= min_val:
                start_legs.append(leg)
    start_legs.sort(key=lambda leg: (leg.timestamp, -leg.value, leg.tx_id))

    candidates_found = []
    for first_leg in start_legs:
        # Trace greedy longest/strongest continuation path from first_leg
        path_addrs = [first_leg.sender, first_leg.receiver]
        path_txs = [first_leg.tx_id]
        ratios: List[float] = []
        residuals: List[float] = []
        timings: List[float] = []
        rel_statuses: Set[str] = {first_leg.relationship_status}

        curr_addr = first_leg.receiver
        curr_val = first_leg.value
        curr_ts = first_leg.timestamp.timestamp()

        while len(path_addrs) < 15:
            next_hops = _find_next_hops(curr_addr, curr_val, curr_ts)
            # Filter out cycles
            next_hops = [h for h in next_hops if h[0].receiver not in path_addrs]
            if not next_hops:
                break
            # Pick highest continuation ratio hop
            best_leg, ratio, residual = max(next_hops, key=lambda item: item[1])
            dt = best_leg.timestamp.timestamp() - curr_ts
            path_addrs.append(best_leg.receiver)
            path_txs.append(best_leg.tx_id)
            ratios.append(ratio)
            residuals.append(residual)
            timings.append(dt)
            rel_statuses.add(best_leg.relationship_status)

            curr_addr = best_leg.receiver
            curr_val = best_leg.value
            curr_ts = best_leg.timestamp.timestamp()

        if len(path_txs) >= cfg.min_hops:
            candidates_found.append(
                (path_addrs, path_txs, ratios, residuals, timings, rel_statuses)
            )

    # Sort longest chains first so sub-chains are always subsumed by their full parent chain
    candidates_found.sort(key=lambda item: len(item[0]), reverse=True)

    for path_addrs, path_txs, ratios, residuals, timings, rel_statuses in candidates_found:
        hop_count = len(path_txs)
        path_key = tuple(path_addrs)
        if any(
            set(path_key).issubset(set(existing)) and len(existing) >= len(path_key)
            for existing in visited_chains
        ):
            continue
        visited_chains.add(path_key)

        avg_ratio = sum(ratios) / len(ratios) if ratios else 0.0
        total_peeled = sum(residuals)
        hop_factor = min(1.0, (hop_count - cfg.min_hops + 1) / 4.0)
        ratio_consistency = 1.0 - min(0.5, max(ratios) - min(ratios)) if len(ratios) >= 2 else 0.75
        pattern_strength = clamp(0.50 + 0.30 * hop_factor + 0.15 * ratio_consistency, 0.50, 0.94)
        severity = "high" if hop_count >= 4 or pattern_strength >= 0.78 else "medium"
        rel_status = "confirmed" if rel_statuses == {"confirmed"} else "inferred"

        findings.append(
            make_finding(
                seq,
                rule_id="PEEL-CHAIN-01",
                rule_version=cfg.rule_version,
                title="Potential peel-chain behaviour",
                category="transaction_pattern",
                severity=severity,  # type: ignore[arg-type]
                confidence=pattern_strength,
                explanation=(
                    f"Detected {hop_count}-hop sequential forwarding path ({' -> '.join(path_addrs)}) "
                    f"with mean continuation ratio {avg_ratio:.2%}, total residual/peeled value "
                    f"{total_peeled:.6g}, and inter-hop delays within {cfg.max_hop_delay_seconds}s."
                ),
                evidence_refs=path_txs,
                limitations=[
                    "Sequential forwarding with change outputs can occur in normal UTXO wallet spending, treasury sweeps, or batch payouts.",
                    "Pattern does not prove criminal intent or single-actor control across every hop.",
                ],
                affected_addresses=path_addrs,
                relationship_status=rel_status,
                metadata={
                    "detected_path": path_addrs,
                    "hop_count": hop_count,
                    "continuation_ratios": [round(r, 4) for r in ratios],
                    "residual_balances": [round(res, 8) for res in residuals],
                    "inter_hop_delays_seconds": [round(t, 2) for t in timings],
                    "pattern_strength": round(pattern_strength, 4),
                },
            )
        )

    return findings
