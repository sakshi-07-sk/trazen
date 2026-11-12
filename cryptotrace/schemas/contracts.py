"""Integration Contracts for CryptoTrace Subsystems.

Provides explicit, frozen interfaces for peer engineers:
- Role 2 (ML / Forensic Detection): Consumes Graph (GraphNode, GraphEdge, TransactionGraph) and CanonicalTransaction.
- Role 3 (Threat Intelligence & Scoring): Consumes CanonicalTransaction, DataSourceProvenance, and TokenTransfer.
- Role 4 (Web Frontend Client): Consumes Investigation API payloads, TransactionSummary, FlowAnalysis, and Paginated responses.
"""

from typing import Generic, List, TypeVar
from pydantic import BaseModel, Field

from cryptotrace.schemas.common import BlockchainType, EdgeType, NodeType, TransactionStatus
from cryptotrace.schemas.graph import (
    FlowAnalysis,
    FlowMetric,
    GraphEdge,
    GraphNode,
    MultiHopTraversalRequest,
    MultiHopTraversalResult,
    TransactionGraph,
)
from cryptotrace.schemas.investigation import (
    InvestigationAnalyzeRequest,
    InvestigationAnalyzeResponse,
    InvestigationCreate,
    InvestigationResponse,
    InvestigationStatus,
)
from cryptotrace.schemas.provenance import DataSourceProvenance
from cryptotrace.schemas.token import TokenTransfer
from cryptotrace.schemas.transaction import CanonicalTransaction, TransactionSummary
from cryptotrace.schemas.utxo import UTXOInput, UTXOOutput, UTXORecord
from cryptotrace.schemas.wallet import WalletProfile, WalletSummary

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standardized envelope for paginated collections consumed by Role 4."""

    items: List[T]
    total: int = Field(..., ge=0, description="Total matching records count")
    page: int = Field(..., ge=1, description="Current page number (1-indexed)")
    page_size: int = Field(..., ge=1, le=200, description="Items returned per page")
    has_more: bool = Field(..., description="Whether subsequent pages exist")


class HealthCheckResponse(BaseModel):
    """Health check payload."""

    status: str = "healthy"
    version: str = "0.1.0"
    app_env: str = "development"
    database_connected: bool = True
    fixture_mode_enabled: bool = True


# Explicit public contract exports
__all__ = [
    # Common
    "BlockchainType",
    "TransactionStatus",
    "NodeType",
    "EdgeType",
    # Provenance
    "DataSourceProvenance",
    # UTXO & Token
    "UTXOInput",
    "UTXOOutput",
    "UTXORecord",
    "TokenTransfer",
    # Transactions
    "CanonicalTransaction",
    "TransactionSummary",
    # Wallets
    "WalletProfile",
    "WalletSummary",
    # Graph Engine (Role 2)
    "GraphNode",
    "GraphEdge",
    "TransactionGraph",
    "MultiHopTraversalRequest",
    "MultiHopTraversalResult",
    "FlowMetric",
    "FlowAnalysis",
    # Investigations (Role 4)
    "InvestigationCreate",
    "InvestigationResponse",
    "InvestigationStatus",
    "InvestigationAnalyzeRequest",
    "InvestigationAnalyzeResponse",
    "PaginatedResponse",
    "HealthCheckResponse",
]
