"""Normalized blockchain, token, provider, and graph input contracts for Role 3."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class TransferType(StrEnum):
    """Supported blockchain transfer types."""

    NATIVE = "native"
    ERC20 = "erc20"
    UTXO = "utxo"
    SPL = "spl"
    TRC20 = "trc20"
    INTERNAL = "internal"
    OTHER = "other"


class AddressContext(BaseModel):
    """Historical wallet context supplied by investigation/provenance state."""

    address: str = Field(..., min_length=1, max_length=256)
    chain: str = Field(..., min_length=1, max_length=64)
    label: str | None = Field(default=None, max_length=256)
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    interaction_count: int = Field(default=0, ge=0)
    is_known_counterparty: bool = False
    is_exchange_hot_wallet: bool = False


class TransactionRecord(BaseModel):
    """Normalized transaction record consumed by validation and threat detectors."""

    tx_hash: str | None = Field(default=None, max_length=256)
    chain: str | None = Field(default=None, max_length=64)
    network: str | None = Field(default=None, max_length=64)
    block_number: int | None = None
    block_hash: str | None = Field(default=None, max_length=256)
    timestamp: datetime | None = None
    confirmations: int | None = None
    status: str | None = Field(default=None, max_length=64)
    from_address: str | None = Field(default=None, max_length=256)
    to_address: str | None = Field(default=None, max_length=256)
    amount: Decimal | str | int | float | None = None
    raw_amount: str | int | None = None
    asset_symbol: str | None = Field(default=None, max_length=64)
    token_contract: str | None = Field(default=None, max_length=256)
    decimals: int | None = None
    transfer_type: TransferType = TransferType.NATIVE
    memo: str | None = Field(default=None, max_length=4096)
    source_provider: str | None = Field(default=None, max_length=128)
    provenance_id: str | None = Field(default=None, max_length=256)
    is_exchange_transfer: bool = False
    is_airdrop_claim: bool = False
    log_index: int | None = None
    vout: int | None = None


class ProviderObservation(BaseModel):
    """Blockchain response from a provider along with upstream lineage metadata."""

    provider_name: str = Field(..., min_length=1, max_length=128)
    upstream_source: str | None = Field(default=None, max_length=128)
    fetched_at: datetime | None = None
    transaction: dict[str, Any] | None = None
    error: str | None = Field(default=None, max_length=512)


class TokenMetadataInput(BaseModel):
    """Token metadata payload evaluated for impersonation or tampering."""

    chain: str = Field(..., min_length=1, max_length=64)
    contract_address: str | None = Field(default=None, max_length=256)
    symbol: str | None = Field(default=None, max_length=128)
    name: str | None = Field(default=None, max_length=256)
    decimals: int | None = None
    previous_symbol: str | None = Field(default=None, max_length=128)
    previous_name: str | None = Field(default=None, max_length=256)
    previous_decimals: int | None = None
    source_provider: str | None = Field(default=None, max_length=128)
    description: str | None = Field(default=None, max_length=2000)


class GraphNodeInput(BaseModel):
    """Node entry inside an investigation transaction graph."""

    node_id: str = Field(..., min_length=1, max_length=256)
    chain: str | None = Field(default=None, max_length=64)
    node_type: str | None = Field(default=None, max_length=64)
    label: str | None = Field(default=None, max_length=256)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphEdgeInput(BaseModel):
    """Edge entry inside an investigation transaction graph."""

    edge_id: str = Field(..., min_length=1, max_length=256)
    source: str = Field(..., min_length=1, max_length=256)
    target: str = Field(..., min_length=1, max_length=256)
    tx_hash: str | None = Field(default=None, max_length=256)
    chain: str | None = Field(default=None, max_length=64)
    edge_type: str | None = Field(default=None, max_length=64)
    is_confirmed: bool = True
    is_heuristic: bool = False
    block_number: int | None = None
    asset: str | None = Field(default=None, max_length=64)
    token_contract: str | None = Field(default=None, max_length=256)
    amount: Decimal | str | int | float | None = None
    direction: str | None = Field(default=None, max_length=32)
    provenance_ref: str | None = Field(default=None, max_length=256)
    log_index: int | None = None
    vout: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
