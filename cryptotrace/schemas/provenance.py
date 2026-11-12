"""Data provenance schemas tracking origin, provider integrity and timestamps."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class DataSourceProvenance(BaseModel):
    """Immutable audit trail for every fetched blockchain record."""

    provider_name: str = Field(..., description="Provider identifier (e.g. blockstream, etherscan, alchemy, fixture_provider)")
    provider_endpoint: Optional[str] = Field(None, description="API endpoint or RPC method invoked")
    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when data was fetched",
    )
    is_fixture: bool = Field(
        default=False,
        description="Indicates whether this record originated from offline fixtures rather than live node RPC",
    )
    raw_payload_hash: str = Field(
        ...,
        description="SHA-256 cryptographic digest of the raw source payload",
    )
    response_latency_ms: Optional[float] = Field(None, description="Round-trip network latency in milliseconds")
    provider_metadata: Dict[str, Any] = Field(default_factory=dict, description="Headers, rate limit status or provider-specific details")
