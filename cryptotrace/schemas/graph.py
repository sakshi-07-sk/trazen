"""Graph representations: nodes, edges, multi-hop traversals, and flow metrics."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
from cryptotrace.schemas.common import BlockchainType, EdgeType, NodeType


def _utcnow() -> datetime:
    """Return current UTC time as a timezone-aware datetime (replaces deprecated datetime.utcnow)."""
    return datetime.now(timezone.utc)


class GraphNode(BaseModel):
    """Forensic node in the transaction graph."""

    id: str = Field(..., description="Unique node identifier (address or tx_hash)")
    node_type: NodeType = Field(..., description="Classification of the node")
    label: str = Field(..., description="Display label for node")
    blockchain: BlockchainType = Field(..., description="Blockchain name")
    chain_id: str = Field(..., description="Network chain ID")
    properties: Dict[str, Any] = Field(
        default_factory=dict,
        description="Node properties (balance, total_sent, total_received, tx_hash, block, tags)",
    )
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None


class GraphEdge(BaseModel):
    """Directed relationship between graph nodes."""

    id: str = Field(..., description="Unique edge identifier")
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    edge_type: EdgeType = Field(..., description="Edge classification")
    is_confirmed: bool = Field(
        default=True,
        description="True for on-chain confirmed transfers; False for heuristic/bridge correlations",
    )
    is_heuristic: bool = Field(
        default=False,
        description="True if edge represents inferred attribution or clustering heuristic",
    )
    amount: Decimal = Field(..., description="Transferred volume (Decimal)")
    asset_symbol: str = Field(default="NATIVE", description="Asset or token symbol")
    tx_hash: str = Field(..., description="Associated transaction hash for on-chain evidence")
    block_number: Optional[int] = Field(None, description="Block height containing transaction")
    timestamp: Optional[datetime] = Field(None, description="Transaction timestamp (UTC)")
    evidence_reference: str = Field(..., description="Auditable evidence citation (tx_hash, vout, log_index)")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional context (vout, token_contract, etc.)")

    @field_validator("amount", mode="before")
    @classmethod
    def validate_amount(cls, val):
        if val is None:
            return Decimal("0")
        if isinstance(val, (int, float, str)):
            return Decimal(str(val))
        return val


class FlowMetric(BaseModel):
    """Flow summary metrics for an address or cluster."""

    total_inflow: Decimal = Decimal("0")
    total_outflow: Decimal = Decimal("0")
    net_flow: Decimal = Decimal("0")
    inflow_tx_count: int = 0
    outflow_tx_count: int = 0
    unique_counterparties_in: int = 0
    unique_counterparties_out: int = 0


class FlowAnalysis(BaseModel):
    """Comprehensive flow analysis around an investigated entity."""

    target_address: str
    blockchain: BlockchainType
    overall_metrics: FlowMetric
    top_inflow_sources: List[Dict[str, Any]] = Field(default_factory=list)
    top_outflow_destinations: List[Dict[str, Any]] = Field(default_factory=list)
    time_window_start: Optional[datetime] = None
    time_window_end: Optional[datetime] = None


class TransactionGraph(BaseModel):
    """Complete graph payload ready for frontend D3 / Sigma / Cytoscape or ML engines."""

    root_node_id: str
    max_hops: int
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
    node_count: int = 0
    edge_count: int = 0
    filters_applied: Dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=_utcnow)


class MultiHopTraversalRequest(BaseModel):
    """Parameters for multi-hop graph exploration."""

    start_address: str = Field(..., description="Seed address to initiate trace")
    blockchain: BlockchainType = Field(..., description="Chain to traverse ('bitcoin' or 'ethereum')")
    max_hops: int = Field(default=2, ge=1, le=3, description="Hop depth limit (max 3)")
    direction: str = Field(default="both", description="Traversal direction: 'forward', 'backward', 'both'")
    min_amount: Optional[Decimal] = Field(None, description="Filter out transactions below threshold")
    max_amount: Optional[Decimal] = Field(None, description="Filter out transactions above threshold")
    start_time: Optional[datetime] = Field(None, description="Earliest transaction time")
    end_time: Optional[datetime] = Field(None, description="Latest transaction time")
    include_heuristics: bool = Field(default=False, description="Include inferred heuristics like co-spend")
    asset_filter: Optional[str] = Field(None, description="Restrict to specific asset symbol (e.g. BTC, ETH, USDT)")


class MultiHopTraversalResult(BaseModel):
    """Result of multi-hop graph traversal."""

    seed_address: str
    blockchain: BlockchainType
    depth_reached: int
    graph: TransactionGraph
    flow_analysis: Optional[FlowAnalysis] = None
    paths_found: List[List[str]] = Field(
        default_factory=list,
        description="All distinct multi-hop node paths discovered from seed",
    )
