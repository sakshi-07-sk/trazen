"""SQLAlchemy ORM model for Role 3 hash-chained forensic audit events."""

from __future__ import annotations

from sqlalchemy import Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from cryptotrace.db.base import Base


class AuditEventModel(Base):
    """Append-only SHA-256 hash-chained forensic audit log record (Role 3)."""

    __tablename__ = "security_audit_events"
    __table_args__ = (
        UniqueConstraint("investigation_id", "sequence_number", name="uq_sec_audit_inv_seq"),
        UniqueConstraint(
            "investigation_id", "previous_event_hash", name="uq_sec_audit_inv_prev_hash"
        ),
        Index("ix_sec_audit_inv_seq", "investigation_id", "sequence_number"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    investigation_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    actor: Mapped[str] = mapped_column(String(128), nullable=False)
    actor_role: Mapped[str] = mapped_column(String(64), nullable=False, default="system")
    event_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    canonical_payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    timestamp: Mapped[str] = mapped_column(String(64), nullable=False)
    previous_event_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    current_event_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    hash_algorithm: Mapped[str] = mapped_column(String(32), nullable=False)
    serialization_version: Mapped[str] = mapped_column(String(64), nullable=False)
    hash_construction_version: Mapped[str] = mapped_column(String(64), nullable=False)

