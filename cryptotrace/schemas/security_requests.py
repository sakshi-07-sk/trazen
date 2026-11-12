"""API request and response schemas for CryptoTrace Role 3 security endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from cryptotrace.schemas.audit import AuditEventRecord
from cryptotrace.schemas.findings import SecurityFinding
from cryptotrace.schemas.security_common import EpistemicLabel
from cryptotrace.schemas.security_inputs import (
    AddressContext,
    GraphEdgeInput,
    GraphNodeInput,
    ProviderObservation,
    TokenMetadataInput,
    TransactionRecord,
)
from cryptotrace.services.security.blockchain_validator import BlockchainValidationReport
from cryptotrace.services.security.security_guardrails import (
    AIOutputValidationResult,
    PromptInspectionResult,
    ToolValidationResult,
    UntrustedContentItem,
)


class AddressPoisoningRequest(BaseModel):
    """Request to evaluate address poisoning and look-alike wallet risks."""

    investigation_id: str = Field(..., min_length=1, max_length=128)
    target_wallet: str = Field(..., min_length=1, max_length=256)
    chain: str = Field(..., min_length=1, max_length=64)
    transactions: list[TransactionRecord] = Field(default_factory=list, max_length=2000)
    known_counterparties: list[AddressContext] = Field(default_factory=list, max_length=1000)
    report_uncorroborated_lookalikes: bool = False


class DustingAnalysisRequest(BaseModel):
    """Request to analyze transactions for asset-aware dusting patterns."""

    investigation_id: str = Field(..., min_length=1, max_length=128)
    transactions: list[TransactionRecord] = Field(default_factory=list, max_length=2000)
    known_exchange_addresses: list[str] = Field(default_factory=list, max_length=500)


class TokenImpersonationRequest(BaseModel):
    """Request to inspect token metadata for impersonation or tampering."""

    investigation_id: str = Field(..., min_length=1, max_length=128)
    tokens: list[TokenMetadataInput] = Field(..., min_length=1, max_length=500)


class GraphIntegrityRequest(BaseModel):
    """Request to validate investigation graph edges against transaction evidence."""

    investigation_id: str = Field(..., min_length=1, max_length=128)
    nodes: list[GraphNodeInput] = Field(default_factory=list, max_length=5000)
    edges: list[GraphEdgeInput] = Field(default_factory=list, max_length=5000)
    evidence_transactions: list[TransactionRecord] = Field(default_factory=list, max_length=5000)
    verified_transactions: list[TransactionRecord] = Field(default_factory=list, max_length=5000)
    require_node_membership: bool = True
    require_provenance_ref: bool = False


class GraphIntegrityResponse(BaseModel):
    """Response summarizing NetworkX graph integrity checks and findings."""

    investigation_id: str
    node_count: int
    edge_count: int
    validated_edge_count: int
    flagged_edge_count: int
    duplicate_edge_count: int
    is_integrity_clean: bool
    findings: list[SecurityFinding] = Field(default_factory=list)


class SecurityFindingsResponse(BaseModel):
    """Standard Role 3 security findings response envelope."""

    investigation_id: str
    total_findings: int
    findings: list[SecurityFinding] = Field(default_factory=list)
    shared_findings: list[dict[str, Any]] = Field(default_factory=list)


class InvestigationSecurityScanResponse(BaseModel):
    """End-to-end Role 3 security & integrity scan summary for a persisted investigation."""

    investigation_id: str
    target_address: str
    blockchain: str
    transactions_evaluated: int
    tokens_evaluated: int
    graph_integrity: dict[str, Any]
    validation_summary: dict[str, int]
    total_findings: int
    findings: list[SecurityFinding] = Field(default_factory=list)
    shared_findings: list[dict[str, Any]] = Field(default_factory=list)


class BlockchainValidationRequest(BaseModel):
    """Request to validate a blockchain transaction and optional provider observations."""

    investigation_id: str = Field(..., min_length=1, max_length=128)
    transaction: TransactionRecord
    provider_observations: list[ProviderObservation] = Field(default_factory=list, max_length=20)
    require_independent_verification: bool = False


class BlockchainValidationAPIResponse(BaseModel):
    """API response wrapping BlockchainValidationReport."""

    investigation_id: str
    report: BlockchainValidationReport


class TraceAIInspectRequest(BaseModel):
    """Request to inspect analyst prompt and untrusted blockchain/document context."""

    investigation_id: str = Field(..., min_length=1, max_length=128)
    user_prompt: str = Field(..., max_length=8000)
    untrusted_items: list[UntrustedContentItem] = Field(default_factory=list, max_length=200)


class TraceAIToolValidationRequest(BaseModel):
    """Request to validate a proposed TraceAI tool invocation."""

    investigation_id: str = Field(..., min_length=1, max_length=128)
    tool_name: str = Field(..., min_length=1, max_length=128)
    arguments: dict[str, Any] = Field(default_factory=dict)


class TraceAIOutputValidationRequest(BaseModel):
    """Request to validate TraceAI output grounding, citations, and confidentiality."""

    investigation_id: str = Field(..., min_length=1, max_length=128)
    response_text: str = Field(..., max_length=32000)
    cited_evidence_refs: list[str] = Field(default_factory=list, max_length=500)
    allowed_evidence_refs: list[str] = Field(default_factory=list, max_length=2000)
    epistemic_label: EpistemicLabel = EpistemicLabel.SUSPICIOUS_INDICATOR


class AuditHistoryResponse(BaseModel):
    """Paginated forensic audit history for an investigation."""

    investigation_id: str
    total_returned: int
    events: list[AuditEventRecord] = Field(default_factory=list)


__all__ = [
    "AIOutputValidationResult",
    "AddressPoisoningRequest",
    "AuditHistoryResponse",
    "BlockchainValidationAPIResponse",
    "BlockchainValidationRequest",
    "DustingAnalysisRequest",
    "GraphIntegrityRequest",
    "GraphIntegrityResponse",
    "InvestigationSecurityScanResponse",
    "PromptInspectionResult",
    "SecurityFindingsResponse",
    "TokenImpersonationRequest",
    "ToolValidationResult",
    "TraceAIInspectRequest",
    "TraceAIOutputValidationRequest",
    "TraceAIToolValidationRequest",
]
