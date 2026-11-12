"""Suspicious transaction structuring (smurfing & rapid pass-through) detector."""

from __future__ import annotations

import statistics
from typing import List

from forensics.config import StructuringConfig
from forensics.detectors.base import FindingIdSequence, clamp, make_finding
from forensics.graph.index import InvestigationGraphIndex, TransferLeg
from forensics.schemas.output import ForensicFinding


EXCLUDED_STRUCTURING_CATEGORIES = {
    "exchange",
    "cex",
    "payroll",
    "merchant",
    "payment_processor",
    "defi_router",
    "mixer",
}


def _find_burst_window(
    legs: List[TransferLeg], max_window_sec: int, min_count: int
) -> List[TransferLeg]:
    """Return the densest sliding time window of legs meeting min_count."""
    if len(legs) < min_count:
        return []
    best_window: List[TransferLeg] = []
    left = 0
    for right in range(len(legs)):
        while (
            legs[right].timestamp - legs[left].timestamp
        ).total_seconds() > max_window_sec:
            left += 1
        window = legs[left : right + 1]
        if len(window) >= min_count and len(window) > len(best_window):
            best_window = window
    return best_window


def detect_structuring(
    index: InvestigationGraphIndex,
    cfg: StructuringConfig,
    seq: FindingIdSequence,
) -> List[ForensicFinding]:
    """Detect threshold-avoidance splitting, similar small-value bursts, and rapid pass-through."""
    chain_cfg = cfg.for_chain(index.chain)
    findings: List[ForensicFinding] = []

    for addr in sorted(index.all_addresses):
        if index.has_category(addr, EXCLUDED_STRUCTURING_CATEGORIES):
            continue

        outbound = index.outbound_legs.get(addr, [])
        inbound = index.inbound_legs.get(addr, [])

        # 1. Repeated small/threshold-avoidance splits in burst window
        burst = _find_burst_window(
            outbound, chain_cfg.max_burst_window_seconds, chain_cfg.min_split_count
        )
        if burst:
            vals = [leg.value for leg in burst if leg.value > 0]
            if len(vals) >= chain_cfg.min_split_count:
                mean_val = statistics.fmean(vals)
                cv = (statistics.pstdev(vals) / mean_val) if mean_val > 0 and len(vals) >= 2 else 0.0

                low_band = (
                    chain_cfg.reporting_reference_threshold
                    * chain_cfg.threshold_avoidance_lower_ratio
                )
                high_band = (
                    chain_cfg.reporting_reference_threshold
                    * chain_cfg.threshold_avoidance_upper_ratio
                )
                near_threshold_count = sum(1 for v in vals if low_band <= v <= high_band)
                small_count = sum(1 for v in vals if v <= chain_cfg.small_tx_upper_bound)

                is_threshold_avoidance = near_threshold_count >= chain_cfg.min_split_count
                is_similar_small_split = (
                    small_count >= chain_cfg.min_split_count
                    and cv <= chain_cfg.min_value_similarity_cv
                )

                if is_threshold_avoidance or is_similar_small_split:
                    span_sec = (burst[-1].timestamp - burst[0].timestamp).total_seconds()
                    conf = clamp(
                        0.64
                        + (0.12 if is_threshold_avoidance else 0.0)
                        + (0.08 if cv <= 0.08 else 0.0)
                        + 0.02 * (len(vals) - chain_cfg.min_split_count),
                        0.60,
                        0.90,
                    )
                    findings.append(
                        make_finding(
                            seq,
                            rule_id="STRUCTURING-SPLIT-01",
                            rule_version=cfg.rule_version,
                            title="Potential transaction structuring / splitting burst",
                            category="transaction_pattern",
                            severity="high" if is_threshold_avoidance else "medium",
                            confidence=conf,
                            explanation=(
                                f"Address {addr} executed {len(vals)} outbound transfers within "
                                f"{span_sec:.0f}s (mean {mean_val:.4g}, CV {cv:.3f}; "
                                f"{near_threshold_count} near threshold {chain_cfg.reporting_reference_threshold:.4g})."
                            ),
                            evidence_refs=[leg.tx_id for leg in burst],
                            limitations=[
                                "Configured chain thresholds are analytical heuristics and not statutory AML determinations.",
                                "Automated disbursements, DCA scripts, or fee-splitting can mimic structuring bursts.",
                            ],
                            affected_addresses=[addr],
                            relationship_status="confirmed",
                            metadata={
                                "chain": index.chain,
                                "burst_count": len(vals),
                                "mean_value": round(mean_val, 8),
                                "value_cv": round(cv, 4),
                                "near_threshold_count": near_threshold_count,
                                "burst_span_seconds": round(span_sec, 2),
                            },
                        )
                    )

        # 2. Rapid aggregation and forwarding (pass-through layering)
        if len(inbound) >= 1 and len(outbound) >= 2:
            total_in = sum(leg.value for leg in inbound)
            if total_in <= 0:
                continue
            first_in_ts = inbound[0].timestamp
            last_in_ts = inbound[-1].timestamp
            rapid_out = [
                leg
                for leg in outbound
                if 0 <= (leg.timestamp - first_in_ts).total_seconds() <= chain_cfg.rapid_passthrough_window_seconds
                or 0 <= (leg.timestamp - last_in_ts).total_seconds() <= chain_cfg.rapid_passthrough_window_seconds
            ]
            rapid_out_val = sum(leg.value for leg in rapid_out)
            passthrough_ratio = rapid_out_val / total_in
            if (
                len(rapid_out) >= 2
                and passthrough_ratio >= chain_cfg.rapid_passthrough_min_ratio
                and passthrough_ratio <= 1.05
            ):
                findings.append(
                    make_finding(
                        seq,
                        rule_id="STRUCTURING-PASSTHROUGH-01",
                        rule_version=cfg.rule_version,
                        title="Rapid aggregation and split forwarding",
                        category="transaction_pattern",
                        severity="medium",
                        confidence=clamp(0.65 + 0.05 * len(rapid_out), 0.65, 0.87),
                        explanation=(
                            f"Address {addr} aggregated {total_in:.4g} across {len(inbound)} inbound transfer(s) "
                            f"and forwarded {passthrough_ratio:.1%} across {len(rapid_out)} outbound transfers "
                            f"within {chain_cfg.rapid_passthrough_window_seconds}s."
                        ),
                        evidence_refs=[leg.tx_id for leg in inbound] + [leg.tx_id for leg in rapid_out],
                        limitations=[
                            "Rapid pass-through can occur in payment routers, escrow contracts, or wallet migrations."
                        ],
                        affected_addresses=[addr],
                        relationship_status="confirmed",
                        metadata={
                            "passthrough_ratio": round(passthrough_ratio, 4),
                            "inbound_count": len(inbound),
                            "rapid_outbound_count": len(rapid_out),
                        },
                    )
                )

    return findings
