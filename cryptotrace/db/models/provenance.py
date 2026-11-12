"""Data Source Provenance ORM Model."""

from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import DateTime, Float, Index, JSON, String
from sqlalchemy.orm import Mapped, mapped_column
from cryptotrace.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ProvenanceModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Cryptographic audit trail tracking source data origin and integrity."""

    __tablename__ = "data_provenance"

    record_type: Mapped[str] = mapped_column(String(50), nullable=False)
    record_identifier: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    provider_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    provider_endpoint: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_fixture: Mapped[bool] = mapped_column(default=False, nullable=False, index=True)
    raw_payload_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    response_latency_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    provider_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    __table_args__ = (
        Index("idx_prov_record_ident", "record_type", "record_identifier"),
        Index("idx_prov_provider_time", "provider_name", "retrieved_at"),
    )
