"""Investigation lifecycle models and API payloads."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from cryptotrace.schemas.common import BlockchainType
from cryptotrace.schemas.graph import FlowAnalysis, TransactionGraph
from cryptotrace.schemas.transaction import TransactionSummary


class InvestigationCreate(BaseModel):
    """Payload to launch a new blockchain forensic investigation."""

    title: str = Field(..., min_length=3, max_length=150, description="Investigation title")
    description: Optional[str] = Field(None, max_length=1000, description="Detailed case notes")
    blockchain: BlockchainType = Field(..., description="Target blockchain: 'bitcoin' or 'ethereum'")
    target_address: str = Field(..., description="Seed wallet or smart contract address under investigation")
    max_hops: int = Field(default=2, ge=1, le=3, description="Exploration depth (1-3 hops)")
    min_amount: Optional[Decimal] = Field(None, ge=0, description="Minimum transaction filter")
    max_amount: Optional[Decimal] = Field(None, ge=0, description="Maximum transaction filter")
    start_time: Optional[datetime] = Field(None, description="Start date filter")
    end_time: Optional[datetime] = Field(None, description="End date filter")
    tags: List[str] = Field(default_factory=list, description="Investigation tags")


class InvestigationStatus(BaseModel):
    """Execution status of an ongoing or completed investigation."""

    id: str
    title: str
    blockchain: BlockchainType
    target_address: str
    status: str = Field(..., description="'created', 'ingesting', 'analyzing', 'completed', 'failed'")
    total_transactions_ingested: int = 0
    total_nodes: int = 0
    total_edges: int = 0
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None


class InvestigationResponse(BaseModel):
    """Complete investigation record with stats."""

    id: str
    title: str
    description: Optional[str]
    blockchain: BlockchainType
    target_address: str
    max_hops: int
    status: str
    total_transactions_ingested: int
    total_nodes: int
    total_edges: int
    created_at: datetime
    updated_at: datetime
    parameters: Dict[str, Any] = Field(default_factory=dict)


class InvestigationAnalyzeRequest(BaseModel):
    """Trigger on-demand multi-hop graph calculation or re-analysis."""

    max_hops: Optional[int] = Field(None, ge=1, le=3)
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    include_heuristics: bool = False


class InvestigationAnalyzeResponse(BaseModel):
    """Forensic analysis outcome."""

    investigation_id: str
    status: str
    nodes_discovered: int
    edges_discovered: int
    flow_analysis: FlowAnalysis
    execution_time_ms: float
    analyzed_at: datetime
