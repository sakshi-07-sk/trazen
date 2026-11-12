"""Security finding interface compatible with Role 1, Role 2, and Role 4 consumers."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from cryptotrace.schemas.security_common import (
    EpistemicLabel,
    EvidenceReference,
    FindingCategory,
    Severity,
    ValidationStatus,
)


def utc_now() -> datetime:
    """Return timezone-aware UTC timestamp."""
    return datetime.now(UTC)


class SecurityFinding(BaseModel):
    """Explainable security or forensic integrity finding produced by Role 3 detectors."""

    finding_id: str = Field(default_factory=lambda: str(uuid4()))
    investigation_id: str = Field(..., min_length=1, max_length=128)
    finding_category: FindingCategory
    finding_type: str = Field(..., min_length=1, max_length=128)
    severity: Severity
    confidence: float = Field(..., ge=0.0, le=1.0)
    epistemic_label: EpistemicLabel = EpistemicLabel.SUSPICIOUS_INDICATOR
    description: str = Field(..., min_length=1, max_length=2000)
    source_address: str | None = Field(default=None, max_length=256)
    suspected_lookalike_address: str | None = Field(default=None, max_length=256)
    similarity_score: float | None = Field(default=None, ge=0.0, le=1.0)
    evidence_references: list[EvidenceReference] = Field(default_factory=list)
    supporting_transaction_refs: list[str] = Field(default_factory=list)
    detection_source: str = Field(..., min_length=1, max_length=128)
    detection_timestamp: datetime = Field(default_factory=utc_now)
    validation_status: ValidationStatus = ValidationStatus.UNVERIFIED
    explanation: str = Field(..., min_length=1, max_length=4000)
    limitations: list[str] = Field(default_factory=list)
    recommended_action: str = Field(..., min_length=1, max_length=1000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SharedFindingAdapter:
    """Adapts Role 3 SecurityFinding models for Role 1/Role 2/Role 4 shared Finding consumers."""

    @staticmethod
    def to_shared_finding_dict(finding: SecurityFinding) -> dict[str, Any]:
        """Serialize a SecurityFinding into a flat, Role-4-friendly shared Finding shape."""
        return {
            "finding_id": finding.finding_id,
            "investigation_id": finding.investigation_id,
            "finding_category": finding.finding_category.value,
            "finding_type": finding.finding_type,
            "severity": finding.severity.value,
            "confidence": finding.confidence,
            "epistemic_label": finding.epistemic_label.value,
            "description": finding.description,
            "evidence_references": [ref.model_dump() for ref in finding.evidence_references],
            "supporting_transaction_refs": list(finding.supporting_transaction_refs),
            "detection_source": finding.detection_source,
            "detection_timestamp": finding.detection_timestamp.isoformat(),
            "validation_status": finding.validation_status.value,
            "explanation": finding.explanation,
            "limitations": list(finding.limitations),
            "recommended_action": finding.recommended_action,
            "details": {
                "source_address": finding.source_address,
                "suspected_lookalike_address": finding.suspected_lookalike_address,
                "similarity_score": finding.similarity_score,
                **finding.metadata,
            },
        }
