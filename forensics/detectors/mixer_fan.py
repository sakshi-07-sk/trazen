"""Fan-in, fan-out, and mixer-signature detectors with high-volume benign guards."""

from __future__ import annotations

from collections import Counter
import statistics
from typing import Dict, List

from forensics.config import MixerFanConfig
from forensics.detectors.base import FindingIdSequence, clamp, make_finding
from forensics.features.extractor import extract_wallet_features
from forensics.graph.index import InvestigationGraphIndex
from forensics.schemas.output import ForensicFinding


BENIGN_HIGH_VOLUME_CATEGORIES = {
    "exchange",
    "cex",
    "merchant",
    "payment_processor",
    "payroll",
    "defi_router",
    "airdrop",
}


def _equal_denomination_ratio(values: List[float], tolerance: float) -> tuple[float, float | None]:
    """Compute fraction of transfers matching the dominant repeated value denomination."""
    positive = [v for v in values if v > 0]
    if len(positive) < 3:
        return 0.0, None

    best_count = 0
    best_anchor = None
    for anchor in positive:
        count = sum(1 for v in positive if abs(v - anchor) <= max(1e-9, anchor * tolerance))
        if count > best_count:
            best_count = count
            best_anchor = anchor
    return best_count / len(positive), best_anchor


def _median_turnaround_seconds(index: InvestigationGraphIndex, address: str) -> float | None:
    inbound = index.inbound_legs.get(address, [])
    outbound = index.outbound_legs.get(address, [])
    if not inbound or not outbound:
        return None
    delays: List[float] = []
    for in_leg in inbound:
        for out_leg in outbound:
            dt = (out_leg.timestamp - in_leg.timestamp).total_seconds()
            if 0 <= dt <= 86400:
                delays.append(dt)
                break
    return float(statistics.median(delays)) if delays else None


def detect_mixer_and_fan_patterns(
    index: InvestigationGraphIndex,
    cfg: MixerFanConfig,
    seq: FindingIdSequence,
) -> List[ForensicFinding]:
    """Detect fan-in aggregation, fan-out distribution, and mixer signatures safely."""
    findings: List[ForensicFinding] = []

    for addr in sorted(index.all_addresses):
        feat = extract_wallet_features(index, addr)
        inbound = index.inbound_legs.get(addr, [])
        outbound = index.outbound_legs.get(addr, [])
        in_txs = [leg.tx_id for leg in inbound]
        out_txs = [leg.tx_id for leg in outbound]
        is_labelled_mixer = index.has_category(addr, {"mixer"})
        is_benign_hub = index.has_category(addr, BENIGN_HIGH_VOLUME_CATEGORIES)

        # 1. Explicit Mixer Signature Analysis
        # NEVER classify as mixer merely because inbound & outbound counts are high!
        if (
            feat.inbound_tx_count >= cfg.mixer_min_inbound
            and feat.outbound_tx_count >= cfg.mixer_min_outbound
        ) or is_labelled_mixer:
            all_vals = [leg.value for leg in inbound + outbound]
            denom_ratio, dominant_denom = _equal_denomination_ratio(
                all_vals, cfg.mixer_equal_denomination_tolerance
            )
            turnaround = _median_turnaround_seconds(index, addr)
            has_equal_denom = denom_ratio >= cfg.mixer_min_equal_denomination_ratio
            has_rapid_turnaround = (
                turnaround is not None and turnaround <= cfg.mixer_max_turnaround_seconds
            )
            no_value_variance = feat.tx_value_cv <= 0.12 and len(all_vals) >= 6

            # Count interactions with labelled mixer contracts/pools
            mixer_cp_txs = [
                leg.tx_id
                for leg in inbound + outbound
                if index.has_category(leg.sender, {"mixer"})
                or index.has_category(leg.receiver, {"mixer"})
            ]

            signature_count = sum(
                [has_equal_denom, has_rapid_turnaround and no_value_variance, is_labelled_mixer]
            )

            # Safeguard: labelled exchanges/merchants/DeFi routers with varied values are NOT mixers
            if not is_benign_hub and (
                is_labelled_mixer or (has_equal_denom and (has_rapid_turnaround or len(all_vals) >= 8))
            ):
                conf = 0.58 + 0.14 * signature_count
                if is_labelled_mixer:
                    conf = max(conf, 0.85)
                findings.append(
                    make_finding(
                        seq,
                        rule_id="MIXER-PATTERN-01",
                        rule_version=cfg.rule_version,
                        title="Potential mixer or pooling signature detected",
                        category="mixer_analysis",
                        severity="high" if is_labelled_mixer or denom_ratio >= 0.75 else "medium",
                        confidence=clamp(conf, 0.5, 0.93),
                        explanation=(
                            f"Address {addr} shows {feat.inbound_tx_count} inbound and "
                            f"{feat.outbound_tx_count} outbound transfers with mixing indicators: "
                            f"equal-denomination ratio {denom_ratio:.2%}"
                            + (f" (~{dominant_denom:.6g})" if dominant_denom else "")
                            + (
                                f", median turnaround {turnaround:.0f}s"
                                if turnaround is not None
                                else ""
                            )
                            + (", labelled mixer entity" if is_labelled_mixer else "")
                            + "."
                        ),
                        evidence_refs=in_txs + out_txs,
                        limitations=[
                            "Mixer interaction or pool-like behaviour is a privacy indicator and does NOT equate to criminality.",
                            "Fixed-price token sales, NFT mints, or staking pools can also exhibit uniform denominations.",
                        ],
                        affected_addresses=[addr],
                        relationship_status="confirmed" if is_labelled_mixer else "inferred",
                        metadata={
                            "equal_denomination_ratio": round(denom_ratio, 4),
                            "dominant_denomination": dominant_denom,
                            "median_turnaround_seconds": turnaround,
                            "is_labelled_mixer": is_labelled_mixer,
                        },
                    )
                )

            # Separate rule for wallets repeatedly interacting with a labelled mixer service
            if mixer_cp_txs and not is_labelled_mixer and not is_benign_hub:
                findings.append(
                    make_finding(
                        seq,
                        rule_id="MIXER-EXPOSURE-01",
                        rule_version=cfg.rule_version,
                        title="Repeated interaction with labelled mixer service",
                        category="mixer_analysis",
                        severity="medium",
                        confidence=0.84,
                        explanation=(
                            f"Address {addr} participated in {len(set(mixer_cp_txs))} transaction(s) "
                            "with a labelled mixer address."
                        ),
                        evidence_refs=mixer_cp_txs,
                        limitations=[
                            "Mixer exposure indicates privacy tool usage and must not be equated with criminal guilt without corroborating evidence."
                        ],
                        affected_addresses=[addr],
                        relationship_status="confirmed",
                    )
                )

        # Check mixer exposure even when wallet has fewer than 4 inbound/outbound txs
        elif not is_labelled_mixer and not is_benign_hub:
            mixer_cp_txs = [
                leg.tx_id
                for leg in inbound + outbound
                if index.has_category(leg.sender, {"mixer"})
                or index.has_category(leg.receiver, {"mixer"})
            ]
            if len(set(mixer_cp_txs)) >= 2:
                findings.append(
                    make_finding(
                        seq,
                        rule_id="MIXER-EXPOSURE-01",
                        rule_version=cfg.rule_version,
                        title="Repeated interaction with labelled mixer service",
                        category="mixer_analysis",
                        severity="medium",
                        confidence=0.82,
                        explanation=(
                            f"Address {addr} interacted {len(set(mixer_cp_txs))} times with a labelled mixer service."
                        ),
                        evidence_refs=mixer_cp_txs,
                        limitations=[
                            "Mixer exposure indicates privacy tool usage and must not be equated with criminal guilt."
                        ],
                        affected_addresses=[addr],
                        relationship_status="confirmed",
                    )
                )

        # Skip pure fan-in/fan-out alerts on verified benign high-volume hubs (exchanges, payroll, merchants)
        if is_benign_hub:
            continue

        # Skip collaborative multi-party UTXO transactions (e.g. CoinJoin) where fan-out reflects pooled outputs
        utxo_txs = index.utxo_txs_by_address.get(addr, [])
        if utxo_txs and all(
            tx.is_collaborative_hint is True
            or (len({i.address for i in tx.inputs}) >= 3 and len({o.address for o in tx.outputs}) >= 3)
            for tx in utxo_txs
        ):
            continue

        # 2. Fan-In Aggregation Detector (many unique senders -> 1 collector, low outbound dispersion)
        if (
            feat.unique_senders >= cfg.fan_in_min_unique_senders
            and feat.fan_in_ratio >= cfg.fan_in_min_ratio
            and feat.unique_receivers <= max(2, feat.unique_senders // 3)
        ):
            conf = clamp(0.60 + 0.04 * (feat.unique_senders - cfg.fan_in_min_unique_senders), 0.60, 0.88)
            findings.append(
                make_finding(
                    seq,
                    rule_id="FAN-IN-01",
                    rule_version=cfg.rule_version,
                    title="High fan-in fund aggregation pattern",
                    category="transaction_pattern",
                    severity="medium" if feat.unique_senders < 10 else "high",
                    confidence=conf,
                    explanation=(
                        f"Address {addr} received transfers from {feat.unique_senders} unique senders "
                        f"(fan-in ratio {feat.fan_in_ratio:.2f}) while forwarding to only "
                        f"{feat.unique_receivers} receiver(s)."
                    ),
                    evidence_refs=in_txs + out_txs,
                    limitations=[
                        "Fan-in aggregation can reflect legitimate merchant checkout, crowdfunding, or exchange deposit sweeping."
                    ],
                    affected_addresses=[addr],
                    relationship_status="confirmed",
                    metadata={
                        "unique_senders": feat.unique_senders,
                        "unique_receivers": feat.unique_receivers,
                        "fan_in_ratio": feat.fan_in_ratio,
                        "total_inflow": feat.total_inflow,
                    },
                )
            )

        # 3. Fan-Out Distribution Detector (1 distributor -> many unique receivers, low inbound dispersion)
        if (
            feat.unique_receivers >= cfg.fan_out_min_unique_receivers
            and feat.fan_out_ratio >= cfg.fan_out_min_ratio
            and feat.unique_senders <= max(2, feat.unique_receivers // 3)
        ):
            conf = clamp(0.60 + 0.04 * (feat.unique_receivers - cfg.fan_out_min_unique_receivers), 0.60, 0.88)
            findings.append(
                make_finding(
                    seq,
                    rule_id="FAN-OUT-01",
                    rule_version=cfg.rule_version,
                    title="High fan-out fund distribution pattern",
                    category="transaction_pattern",
                    severity="medium" if feat.unique_receivers < 10 else "high",
                    confidence=conf,
                    explanation=(
                        f"Address {addr} distributed funds to {feat.unique_receivers} unique receivers "
                        f"(fan-out ratio {feat.fan_out_ratio:.2f}) from {feat.unique_senders} sender(s)."
                    ),
                    evidence_refs=in_txs + out_txs,
                    limitations=[
                        "Fan-out dispersion can reflect payroll, token airdrops, staking rewards, or exchange withdrawals."
                    ],
                    affected_addresses=[addr],
                    relationship_status="confirmed",
                    metadata={
                        "unique_senders": feat.unique_senders,
                        "unique_receivers": feat.unique_receivers,
                        "fan_out_ratio": feat.fan_out_ratio,
                        "total_outflow": feat.total_outflow,
                    },
                )
            )

    return findings
