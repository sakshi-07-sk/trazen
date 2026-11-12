"""4-dimensional explainable risk and attribution scoring engine."""

from __future__ import annotations

from typing import Any, Dict, List

from forensics.config import RiskScoringConfig
from forensics.detectors.base import clamp
from forensics.features.extractor import extract_wallet_features
from forensics.graph.index import InvestigationGraphIndex
from forensics.schemas.output import (
    ContributingFactor,
    ForensicFinding,
    ReceiverCandidate,
    RiskAssessmentResponse,
    WalletRiskSummary,
)


SEVERITY_NUMERIC = {
    "low": 0.25,
    "medium": 0.55,
    "high": 0.80,
    "critical": 0.95,
}


def _compute_wallet_known_risk_exposure(
    index: InvestigationGraphIndex,
    addr: str,
    cfg: RiskScoringConfig,
) -> tuple[float, List[str]]:
    """Compute hop-decayed proximity to documented risk indicators without equating mixers to crime."""
    notes: List[str] = []
    hit = index.min_hop_distance_to_risk_indicator(addr, max_hops=cfg.max_exposure_hops)
    if hit is None:
        # Check non-illicit mixer proximity separately (capped)
        if index.has_category(addr, {"mixer"}):
            notes.append(
                "Mixer category present without corroborated illicit indicator; exposure capped."
            )
            return min(0.35, cfg.mixer_exposure_cap_without_illicit_link), notes
        return 0.0, notes

    dist, target_addr, lbl = hit
    base = 0.95 if lbl.risk_indicator == "critical" else 0.80
    decayed = base * (cfg.exposure_hop_decay ** dist)
    if not lbl.verified:
        decayed *= 0.80
        notes.append(f"Risk indicator on {target_addr} ({lbl.label}) is unverified.")

    # Never equate mixer exposure alone with criminality
    if lbl.category.lower() == "mixer" and lbl.risk_indicator != "critical":
        decayed = min(decayed, cfg.mixer_exposure_cap_without_illicit_link)
        notes.append(
            "Exposure originates from a mixer label without direct illicit attribution; score capped."
        )

    return clamp(decayed), notes


def compute_risk_assessment(
    index: InvestigationGraphIndex,
    findings: List[ForensicFinding],
    anomaly_details: Dict[str, Dict[str, Any]],
    receivers: List[ReceiverCandidate],
    cfg: RiskScoringConfig,
) -> RiskAssessmentResponse:
    """Compute separate risk priority, attribution confidence, risk exposure, and coverage."""
    coverage_score, coverage_notes = index.compute_investigation_coverage()
    confirmed_ratio = index.confirmed_edge_ratio()

    # Filter actionable findings (safeguard findings are informational, not risk drivers)
    risk_findings = [f for f in findings if f.category != "clustering_safeguard"]
    safeguard_findings = [f for f in findings if f.category == "clustering_safeguard"]

    # Per-wallet risk summaries
    wallet_risks: List[WalletRiskSummary] = []
    wallet_exposures: List[float] = []
    extra_counter_evidence: List[str] = []

    for addr in sorted(index.all_addresses):
        addr_findings = [f for f in risk_findings if addr in f.affected_addresses]
        max_sev = max((SEVERITY_NUMERIC[f.severity] for f in addr_findings), default=0.0)
        finding_density = clamp(len(addr_findings) / 3.0)
        exposure, exp_notes = _compute_wallet_known_risk_exposure(index, addr, cfg)
        wallet_exposures.append(exposure)
        extra_counter_evidence.extend(exp_notes)

        anom = anomaly_details.get(addr, {})
        anom_score = float(anom.get("anomaly_score", 0.0))
        anom_rank = anom.get("priority_rank")

        pw = cfg.priority_weights
        w_priority = clamp(
            pw.get("severity_score", 0.35) * max_sev
            + pw.get("finding_density", 0.20) * finding_density
            + pw.get("known_risk_exposure", 0.25) * exposure
            + pw.get("anomaly_signal", 0.20) * anom_score
        )

        # Attribution confidence per wallet
        mean_f_conf = (
            sum(f.confidence for f in addr_findings) / len(addr_findings)
            if addr_findings
            else confirmed_ratio
        )
        lbl = index.get_primary_label(addr)
        lbl_boost = 0.15 if (lbl and lbl.verified) else 0.0
        w_attr = clamp(0.45 * confirmed_ratio + 0.35 * mean_f_conf + 0.20 * coverage_score + lbl_boost)

        node = index.node_by_address.get(addr)
        w_cov = coverage_score
        w_counter: List[str] = list(exp_notes)
        if node and not node.observed_in_full:
            w_cov *= 0.65
            w_counter.append("Wallet transaction history not observed in full.")
        if index.has_category(addr, {"exchange", "cex", "merchant", "payroll", "defi_router"}):
            w_counter.append(f"Wallet carries benign/commercial service label ({lbl.label if lbl else 'service'}).")

        wallet_risks.append(
            WalletRiskSummary(
                address=addr,
                risk_priority=round(w_priority, 4),
                attribution_confidence=round(w_attr, 4),
                known_risk_exposure=round(exposure, 4),
                investigation_coverage=round(clamp(w_cov), 4),
                anomaly_score=round(anom_score, 4) if addr in anomaly_details else None,
                anomaly_priority_rank=anom_rank,
                supporting_finding_ids=[f.finding_id for f in addr_findings],
                counter_evidence=w_counter,
            )
        )

    wallet_risks.sort(key=lambda w: w.risk_priority, reverse=True)

    # Case-level 4 dimensions
    max_case_sev = max((SEVERITY_NUMERIC[f.severity] for f in risk_findings), default=0.0)
    case_density = clamp(len(risk_findings) / 4.0)
    case_exposure = max(wallet_exposures, default=0.0)
    max_anom = max((float(v.get("anomaly_score", 0.0)) for v in anomaly_details.values()), default=0.0)

    # Dampen anomaly weight when no rule-based findings or risk exposure exist (avoid false alarms on normal graphs)
    effective_anom = max_anom if (risk_findings or case_exposure > 0.0) else max_anom * 0.20

    pw = cfg.priority_weights
    w_sev = pw.get("severity_score", 0.35)
    w_den = pw.get("finding_density", 0.20)
    w_exp = pw.get("known_risk_exposure", 0.25)
    w_ano = pw.get("anomaly_signal", 0.20)

    risk_priority = clamp(
        w_sev * max_case_sev
        + w_den * case_density
        + w_exp * case_exposure
        + w_ano * effective_anom
    )

    # Path continuity from top receiver candidate if available
    top_path_consistency = receivers[0].path_consistency if receivers else confirmed_ratio
    mean_finding_conf = (
        sum(f.confidence for f in risk_findings) / len(risk_findings)
        if risk_findings
        else confirmed_ratio
    )

    aw = cfg.attribution_weights
    w_conf_edge = aw.get("confirmed_edge_ratio", 0.40)
    w_path = aw.get("path_continuity", 0.25)
    w_fconf = aw.get("finding_confidence", 0.20)
    w_cov = aw.get("investigation_coverage", 0.15)

    attribution_confidence = clamp(
        w_conf_edge * confirmed_ratio
        + w_path * top_path_consistency
        + w_fconf * mean_finding_conf
        + w_cov * coverage_score
    )

    contributing_factors = [
        ContributingFactor(
            factor_name="max_finding_severity",
            dimension="risk_priority",
            weight=w_sev,
            raw_value=round(max_case_sev, 4),
            contribution=round(w_sev * max_case_sev, 4),
            explanation="Highest severity among rule-based forensic findings.",
        ),
        ContributingFactor(
            factor_name="finding_density",
            dimension="risk_priority",
            weight=w_den,
            raw_value=round(case_density, 4),
            contribution=round(w_den * case_density, 4),
            explanation=f"{len(risk_findings)} corroborating forensic finding(s) detected.",
        ),
        ContributingFactor(
            factor_name="known_risk_exposure",
            dimension="risk_priority",
            weight=w_exp,
            raw_value=round(case_exposure, 4),
            contribution=round(w_exp * case_exposure, 4),
            explanation="Hop-decayed proximity to documented risk indicators (mixer exposure alone capped).",
        ),
        ContributingFactor(
            factor_name="anomaly_signal",
            dimension="risk_priority",
            weight=w_ano,
            raw_value=round(effective_anom, 4),
            contribution=round(w_ano * effective_anom, 4),
            explanation="Unsupervised Isolation Forest behavioural deviation priority signal.",
        ),
        ContributingFactor(
            factor_name="confirmed_edge_ratio",
            dimension="attribution_confidence",
            weight=w_conf_edge,
            raw_value=round(confirmed_ratio, 4),
            contribution=round(w_conf_edge * confirmed_ratio, 4),
            explanation="Proportion of confirmed vs inferred transaction edges in investigation graph.",
        ),
        ContributingFactor(
            factor_name="top_path_consistency",
            dimension="attribution_confidence",
            weight=w_path,
            raw_value=round(top_path_consistency, 4),
            contribution=round(w_path * top_path_consistency, 4),
            explanation="Continuity and confirmation strength along highest-ranked destination trace path.",
        ),
        ContributingFactor(
            factor_name="investigation_coverage",
            dimension="attribution_confidence",
            weight=w_cov,
            raw_value=round(coverage_score, 4),
            contribution=round(w_cov * coverage_score, 4),
            explanation="Observed completeness of nodes, neighbors, and transaction history.",
        ),
    ]

    counter_evidence: List[str] = []
    if confirmed_ratio < 0.7:
        counter_evidence.append(
            f"Only {confirmed_ratio:.1%} of graph edges are confirmed; remaining links are inferred heuristics."
        )
    if safeguard_findings:
        counter_evidence.append(
            "Collaborative/CoinJoin transaction(s) detected; common-input attribution was intentionally suppressed."
        )
    benign_labelled = [
        lbl.label
        for addr in index.all_addresses
        for lbl in index.get_labels(addr)
        if lbl.category.lower() in {"exchange", "cex", "merchant", "payroll", "defi_router"}
    ]
    if benign_labelled:
        counter_evidence.append(
            f"Graph involves known commercial/service entities ({', '.join(sorted(set(benign_labelled)))})."
        )
    if not risk_findings:
        counter_evidence.append("No suspicious forensic pattern rules triggered on the observed graph.")
    for item in extra_counter_evidence:
        if item not in counter_evidence:
            counter_evidence.append(item)

    limitations = list(coverage_notes) + [
        "Risk priority guides investigative triage; it is NOT a determination of legal guilt or criminality.",
        "Mixer exposure indicates privacy-enhancing tool usage and is never equated with illicit activity alone.",
    ]

    return RiskAssessmentResponse(
        investigation_id=index.case.investigation_id,
        scoring_rule_version=cfg.rule_version,
        risk_priority=round(risk_priority, 4),
        attribution_confidence=round(attribution_confidence, 4),
        known_risk_exposure=round(case_exposure, 4),
        investigation_coverage=round(coverage_score, 4),
        contributing_factors=contributing_factors,
        supporting_finding_ids=[f.finding_id for f in risk_findings],
        counter_evidence=counter_evidence,
        confidence_limitations=limitations,
        probable_end_receivers=receivers,
        wallet_risks=wallet_risks,
    )
