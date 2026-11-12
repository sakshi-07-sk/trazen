"""Dormant-wallet reactivation detector."""

from __future__ import annotations

from typing import List

from forensics.config import GeneralConfig
from forensics.detectors.base import FindingIdSequence, clamp, make_finding
from forensics.graph.index import InvestigationGraphIndex
from forensics.schemas.output import ForensicFinding


def detect_dormant_activations(
    index: InvestigationGraphIndex,
    cfg: GeneralConfig,
    seq: FindingIdSequence,
) -> List[ForensicFinding]:
    """Detect wallets reactivating after extended dormancy with a sudden transfer burst."""
    findings: List[ForensicFinding] = []

    for addr in sorted(index.all_addresses):
        if index.has_category(addr, {"exchange", "cex"}):
            continue

        all_legs = sorted(
            index.inbound_legs.get(addr, []) + index.outbound_legs.get(addr, []),
            key=lambda leg: leg.timestamp,
        )
        if len(all_legs) < 2:
            continue

        for i in range(1, len(all_legs)):
            gap = (all_legs[i].timestamp - all_legs[i - 1].timestamp).total_seconds()
            if gap >= cfg.dormancy_threshold_seconds:
                # Count reactivation burst within 24 hours after wake-up
                wakeup_ts = all_legs[i].timestamp
                burst_legs = [
                    leg
                    for leg in all_legs[i:]
                    if (leg.timestamp - wakeup_ts).total_seconds() <= 86400
                ]
                if len(burst_legs) >= cfg.dormancy_reactivation_min_txs:
                    days = gap / 86400.0
                    conf = clamp(0.68 + 0.04 * min(5, len(burst_legs) - 1), 0.68, 0.88)
                    findings.append(
                        make_finding(
                            seq,
                            rule_id="DORMANT-REACTIVATION-01",
                            rule_version="1.0",
                            title="Dormant wallet reactivation burst",
                            category="behavioural_anomaly",
                            severity="medium" if days < 180 else "high",
                            confidence=conf,
                            explanation=(
                                f"Address {addr} became active after {days:.1f} days of inactivity, "
                                f"executing {len(burst_legs)} transfer(s) within 24 hours of reactivation."
                            ),
                            evidence_refs=[all_legs[i - 1].tx_id] + [leg.tx_id for leg in burst_legs],
                            limitations=[
                                "Cold-storage rotation, long-term vesting, or user wallet recovery can cause legitimate dormant reactivation."
                            ],
                            affected_addresses=[addr],
                            relationship_status="confirmed",
                            metadata={
                                "dormancy_days": round(days, 2),
                                "reactivation_tx_count": len(burst_legs),
                            },
                        )
                    )
                    break

    return findings
