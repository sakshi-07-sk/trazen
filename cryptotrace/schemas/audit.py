"""Pydantic schemas for tamper-evident forensic audit events, verification, and export."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from cryptotrace.schemas.findings import utc_now


class AuditEventCreate(BaseModel):
    """Input payload to append a new tamper-evident audit event."""

    investigation_id: str = Field(..., min_length=1, max_length=128)
    event_type: str = Field(..., min_length=1, max_length=128)
    payload: dict[str, Any] = Field(default_factory=dict)
    actor: str | None = Field(default=None, max_length=128)
    actor_role: str | None = Field(default=None, max_length=64)


class AuditEventRecord(BaseModel):
    """Serialized hash-chained audit event returned by API and export services."""

    event_id: str
    sequence_number: int
    investigation_id: str
    actor: str
    actor_role: str
    event_type: str
    canonical_payload: dict[str, Any]
    canonical_payload_json: str
    payload_hash: str
    timestamp: str
    previous_event_hash: str
    current_event_hash: str
    hash_algorithm: str
    serialization_version: str
    hash_construction_version: str


class AuditVerificationRequest(BaseModel):
    """Request to verify the integrity of an investigation's audit chain."""

    investigation_id: str = Field(..., min_length=1, max_length=128)
    expected_event_count: int | None = Field(default=None, ge=0)
    expected_head_hash: str | None = Field(default=None, min_length=64, max_length=64)


class AuditVerificationReport(BaseModel):
    """Detailed verification report identifying chain integrity or exact tamper point."""

    investigation_id: str
    status: str  # "VERIFIED", "EMPTY", or "TAMPERED"
    is_valid: bool
    total_events_checked: int
    verified_events: int
    failed_events: int
    first_broken_sequence_number: int | None = None
    failure_reason: str | None = None
    expected_previous_hash: str | None = None
    actual_previous_hash: str | None = None
    expected_event_hash: str | None = None
    actual_event_hash: str | None = None
    head_hash: str | None = None
    tail_hash: str | None = None
    verification_timestamp: datetime = Field(default_factory=utc_now)
    integrity_note: str = (
        "Hash chains provide cryptographic tamper-evidence across retained records; "
        "external anchoring or signed exports are required to detect silent tail truncation."
    )


class AuditExportManifest(BaseModel):
    """Self-contained exportable forensic audit history with optional Ed25519 signature."""

    investigation_id: str
    exported_at: datetime = Field(default_factory=utc_now)
    total_events: int
    genesis_hash: str
    head_hash: str | None = None
    tail_hash: str | None = None
    hash_algorithm: str
    serialization_version: str
    hash_construction_version: str
    verification_status: str
    tamper_evident_notice: str = (
        "This hash-chained manifest is tamper-evident, not inherently immutable. "
        "Verify signature and re-run chain verification independently before relying on exported records."
    )
    events: list[AuditEventRecord] = Field(default_factory=list)
    signature_algorithm: str | None = None
    signature_b64: str | None = None
    public_key_pem: str | None = None

