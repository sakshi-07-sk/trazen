"""Input integration schemas supplied by Role 1 (normalized data & graph structures)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


ChainType = Literal["bitcoin", "ethereum", "other"]
RelationshipStatus = Literal["confirmed", "inferred"]


class UTXOEntry(BaseModel):
    """Single input or output leg for UTXO-based chains such as Bitcoin."""

    address: str
    value: float = Field(ge=0.0)
    output_index: Optional[int] = None
    is_change_hint: Optional[bool] = None


class EntityLabel(BaseModel):
    """Attribution or service metadata attached to a wallet or contract address."""

    address: str
    label: str
    category: str = Field(
        description="e.g. exchange, mixer, bridge, sanctioned, ransomware, merchant, payroll, defi_router, unknown"
    )
    risk_indicator: Literal["none", "low", "medium", "high", "critical"] = "none"
    provenance: str = "unverified"
    verified: bool = False
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)


class NormalizedTransaction(BaseModel):
    """Normalized transaction record supplied by Role 1."""

    tx_id: str
    chain: ChainType = "ethereum"
    timestamp: datetime
    block_number: Optional[int] = None

    # Account-based primary fields (also populated as primary summary for UTXO when needed)
    from_address: Optional[str] = None
    to_address: Optional[str] = None
    value: float = Field(default=0.0, ge=0.0)
    fee: float = Field(default=0.0, ge=0.0)
    asset: str = "ETH"

    # UTXO-specific fields (Bitcoin)
    inputs: List[UTXOEntry] = Field(default_factory=list)
    outputs: List[UTXOEntry] = Field(default_factory=list)

    # Account/EVM-specific fields (Ethereum)
    nonce: Optional[int] = None
    is_contract_call: bool = False
    is_token_transfer: bool = False
    is_bridge_interaction: bool = False
    method_signature: Optional[str] = None

    # Relationship & provenance metadata from Role 1 graph engine
    relationship_status: RelationshipStatus = "confirmed"
    is_collaborative_hint: Optional[bool] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GraphNode(BaseModel):
    """Graph node representing an address/wallet or service entity."""

    node_id: str
    address: str
    chain: ChainType = "ethereum"
    role_hint: Optional[str] = None  # e.g. seed, intermediary, sink
    observed_in_full: bool = True
    missing_neighbors_estimated: int = Field(default=0, ge=0)
    labels: List[EntityLabel] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """Directed relationship edge from Role 1's graph engine."""

    edge_id: str
    source: str
    target: str
    tx_ids: List[str] = Field(default_factory=list)
    total_value: float = Field(default=0.0, ge=0.0)
    tx_count: int = Field(default=1, ge=0)
    relationship_status: RelationshipStatus = "confirmed"
    inference_reason: Optional[str] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None


class InvestigationCase(BaseModel):
    """Complete investigation graph and normalized transactions from Role 1."""

    investigation_id: str
    title: str = ""
    chain: ChainType = "ethereum"
    seed_addresses: List[str] = Field(default_factory=list)
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
    transactions: List[NormalizedTransaction] = Field(default_factory=list)
    labels: List[EntityLabel] = Field(default_factory=list)
    expected_trace_hops: Optional[int] = None
    is_graph_complete: bool = True
    missing_data_notes: List[str] = Field(default_factory=list)
