"""Shared output contract schemas for Role 3, Role 4, and API consumers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


SeverityLevel = Literal["low", "medium", "high", "critical"]


class ForensicFinding(BaseModel):
    """Standardized forensic finding matching Section 8 Shared Output Contract."""

    finding_id: str
    rule_id: str
    rule_version: str
    title: str
    category: str
    severity: SeverityLevel
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: str
    evidence_refs: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    affected_addresses: List[str] = Field(default_factory=list)
    relationship_status: Literal["confirmed", "inferred", "mixed"] = "inferred"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ClusterEdgeReason(BaseModel):
    """Explicit reasoning and evidence for linking two addresses in a cluster."""

    address_a: str
    address_b: str
    heuristic: str
    confidence: float = Field(ge=0.0, le=1.0)
    relationship_status: Literal["confirmed", "inferred"] = "inferred"
    reason: str
    evidence_refs: List[str] = Field(default_factory=list)
    counter_evidence: List[str] = Field(default_factory=list)


class ClusterGroup(BaseModel):
    """Candidate wallet cluster with preserved attribution reasons and limitations."""

    cluster_id: str
    addresses: List[str]
    confidence: float = Field(ge=0.0, le=1.0)
    reasons: List[ClusterEdgeReason] = Field(default_factory=list)
    suppressed_coinjoin_txs: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)


class WalletFeatureVector(BaseModel):
    """Reusable wallet-level behavioural feature vector (BTC UTXO & ETH account aware)."""

    address: str
    chain: str
    inbound_tx_count: int = 0
    outbound_tx_count: int = 0
    total_tx_count: int = 0
    unique_senders: int = 0
    unique_receivers: int = 0
    unique_counterparties: int = 0
    total_inflow: float = 0.0
    total_outflow: float = 0.0
    net_flow: float = 0.0
    residual_balance_ratio: float = 0.0
    median_tx_value: float = 0.0
    mean_tx_value: float = 0.0
    tx_value_cv: float = 0.0
    tx_velocity_per_day: float = 0.0
    dormancy_period_seconds: float = 0.0
    fan_in_ratio: float = 0.0
    fan_out_ratio: float = 0.0
    known_service_exposure: float = 0.0
    known_risk_service_exposure: float = 0.0
    bridge_interaction_count: int = 0
    tx_timing_variation_seconds: float = 0.0
    # Chain-specific features
    utxo_avg_inputs: float = 0.0
    utxo_avg_outputs: float = 0.0
    address_reuse_count: int = 0
    contract_interaction_ratio: float = 0.0
    token_transfer_ratio: float = 0.0


class ContributingFactor(BaseModel):
    """Explainable factor contribution to a risk or confidence dimension."""

    factor_name: str
    dimension: str
    weight: float
    raw_value: float
    contribution: float
    explanation: str


class WalletRiskSummary(BaseModel):
    """Per-wallet 4-dimensional risk and attribution assessment."""

    address: str
    risk_priority: float = Field(ge=0.0, le=1.0)
    attribution_confidence: float = Field(ge=0.0, le=1.0)
    known_risk_exposure: float = Field(ge=0.0, le=1.0)
    investigation_coverage: float = Field(ge=0.0, le=1.0)
    anomaly_score: Optional[float] = None
    anomaly_priority_rank: Optional[int] = None
    supporting_finding_ids: List[str] = Field(default_factory=list)
    counter_evidence: List[str] = Field(default_factory=list)


class ReceiverCandidate(BaseModel):
    """Ranked candidate end-receiver destination (never asserts human identity)."""

    rank: int
    candidate_destination: str
    entity_label: Optional[str] = None
    label_provenance: str = "unlabelled"
    trace_path: List[str] = Field(default_factory=list)
    hop_distance: int = 0
    value_received: float = 0.0
    value_proportion: float = Field(ge=0.0, le=1.0)
    ranking_score: float = Field(ge=0.0, le=1.0)
    risk_priority: float = Field(ge=0.0, le=1.0)
    attribution_confidence: float = Field(ge=0.0, le=1.0)
    path_consistency: float = Field(ge=0.0, le=1.0)
    investigation_coverage: float = Field(ge=0.0, le=1.0)
    supporting_finding_ids: List[str] = Field(default_factory=list)
    counter_evidence: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)


class InvestigationFindingsResponse(BaseModel):
    """Response schema for GET /api/v1/investigations/{id}/findings."""

    investigation_id: str
    chain: str
    findings: List[ForensicFinding] = Field(default_factory=list)
    total_count: int = 0
    clusters: List[ClusterGroup] = Field(default_factory=list)
    rule_versions: Dict[str, str] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RiskAssessmentResponse(BaseModel):
    """Response schema for GET /api/v1/investigations/{id}/risk."""

    investigation_id: str
    scoring_rule_version: str
    risk_priority: float = Field(ge=0.0, le=1.0)
    attribution_confidence: float = Field(ge=0.0, le=1.0)
    known_risk_exposure: float = Field(ge=0.0, le=1.0)
    investigation_coverage: float = Field(ge=0.0, le=1.0)
    contributing_factors: List[ContributingFactor] = Field(default_factory=list)
    supporting_finding_ids: List[str] = Field(default_factory=list)
    counter_evidence: List[str] = Field(default_factory=list)
    confidence_limitations: List[str] = Field(default_factory=list)
    probable_end_receivers: List[ReceiverCandidate] = Field(default_factory=list)
    wallet_risks: List[WalletRiskSummary] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CrossCaseFinding(BaseModel):
    """Shared infrastructure or path overlap across multiple investigations."""

    finding: ForensicFinding
    case_ids: List[str]
    shared_addresses: List[str] = Field(default_factory=list)
    common_destinations: List[str] = Field(default_factory=list)
    overlapping_paths: List[List[str]] = Field(default_factory=list)


class CrossCaseAnalysisResponse(BaseModel):
    """Output of cross-case relationship comparison."""

    analyzed_case_ids: List[str]
    cross_case_findings: List[CrossCaseFinding] = Field(default_factory=list)
    ignored_public_hubs: List[str] = Field(default_factory=list)


class EvaluationMetrics(BaseModel):
    """Classification / detection evaluation metrics."""

    model_config = {"protected_namespaces": ()}

    model_name: str
    precision: float
    recall: float
    f1_score: float
    confusion_matrix: List[List[int]]
    support: int
    false_positive_cases: List[str] = Field(default_factory=list)
    false_positive_analysis: List[str] = Field(default_factory=list)


class MLEvaluationReport(BaseModel):
    """Structured ML & heuristic evaluation report with synthetic provenance notice."""

    model_config = {"protected_namespaces": ()}

    dataset_provenance: str
    sample_count: int
    anomaly_prioritization_summary: Dict[str, Any] = Field(default_factory=dict)
    dbscan_cluster_summary: Dict[str, Any] = Field(default_factory=dict)
    baseline_metrics: EvaluationMetrics
    model_metrics: List[EvaluationMetrics] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)


class ForensicAnalysisBundle(BaseModel):
    """Full forensic analysis output produced by ForensicEngine."""

    investigation_id: str
    findings_response: InvestigationFindingsResponse
    risk_response: RiskAssessmentResponse
    wallet_features: Dict[str, WalletFeatureVector] = Field(default_factory=dict)
    anomaly_details: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    dbscan_clusters: Dict[str, int] = Field(default_factory=dict)
