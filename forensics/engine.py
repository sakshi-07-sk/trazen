"""Orchestrating Forensic Intelligence Engine (Role 2)."""

from __future__ import annotations

from typing import Dict, List

from forensics.config import ForensicsConfig, load_config
from forensics.detectors.base import FindingIdSequence
from forensics.detectors.clustering import detect_wallet_clusters
from forensics.detectors.cross_case import analyze_cross_case_relationships
from forensics.detectors.dormancy import detect_dormant_activations
from forensics.detectors.mixer_fan import detect_mixer_and_fan_patterns
from forensics.detectors.peel_chain import detect_peel_chains
from forensics.detectors.structuring import detect_structuring
from forensics.features.extractor import extract_all_wallet_features
from forensics.graph.index import InvestigationGraphIndex
from forensics.ml.anomaly import prioritize_wallet_anomalies
from forensics.ml.clustering import cluster_wallet_behaviours
from forensics.schemas.input import InvestigationCase
from forensics.schemas.output import (
    CrossCaseAnalysisResponse,
    ForensicAnalysisBundle,
    ForensicFinding,
    InvestigationFindingsResponse,
)
from forensics.scoring.ranking import rank_probable_end_receivers
from forensics.scoring.risk import compute_risk_assessment


class ForensicEngine:
    """Deterministic, evidence-driven forensic intelligence engine."""

    def __init__(self, config: ForensicsConfig | None = None) -> None:
        self.config = config or load_config()

    def analyze_case(self, case: InvestigationCase) -> ForensicAnalysisBundle:
        """Run full single-pass indexing, feature extraction, detectors, ML, ranking, and risk."""
        index = InvestigationGraphIndex(case)
        features = extract_all_wallet_features(index)
        seq = FindingIdSequence(prefix="FT", start=1)

        findings: List[ForensicFinding] = []
        clusters, cluster_findings = detect_wallet_clusters(index, self.config.clustering, seq)
        findings.extend(cluster_findings)
        findings.extend(detect_peel_chains(index, self.config.peel_chain, seq))
        findings.extend(detect_mixer_and_fan_patterns(index, self.config.mixer_fan, seq))
        findings.extend(detect_structuring(index, self.config.structuring, seq))
        findings.extend(detect_dormant_activations(index, self.config.general, seq))

        anomaly_details = prioritize_wallet_anomalies(features, self.config.ml)
        dbscan_labels, _ = cluster_wallet_behaviours(features, self.config.ml)

        coverage_score, _ = index.compute_investigation_coverage()
        receivers = rank_probable_end_receivers(
            index=index,
            findings=findings,
            cfg=self.config.receiver_ranking,
            coverage_score=coverage_score,
        )
        risk_response = compute_risk_assessment(
            index=index,
            findings=findings,
            anomaly_details=anomaly_details,
            receivers=receivers,
            cfg=self.config.risk_scoring,
        )

        rule_versions = {
            "clustering": self.config.clustering.rule_version,
            "peel_chain": self.config.peel_chain.rule_version,
            "mixer_fan": self.config.mixer_fan.rule_version,
            "structuring": self.config.structuring.rule_version,
            "risk_scoring": self.config.risk_scoring.rule_version,
            "receiver_ranking": self.config.receiver_ranking.rule_version,
        }

        findings_response = InvestigationFindingsResponse(
            investigation_id=case.investigation_id,
            chain=case.chain,
            findings=findings,
            total_count=len(findings),
            clusters=clusters,
            rule_versions=rule_versions,
        )

        return ForensicAnalysisBundle(
            investigation_id=case.investigation_id,
            findings_response=findings_response,
            risk_response=risk_response,
            wallet_features=features,
            anomaly_details=anomaly_details,
            dbscan_clusters=dbscan_labels,
        )

    def analyze_cross_case(self, cases: List[InvestigationCase]) -> CrossCaseAnalysisResponse:
        """Compare multiple investigation graphs for shared infrastructure and overlapping paths."""
        indices: Dict[str, InvestigationGraphIndex] = {
            case.investigation_id: InvestigationGraphIndex(case) for case in cases
        }
        return analyze_cross_case_relationships(cases, self.config.cross_case, indices=indices)
