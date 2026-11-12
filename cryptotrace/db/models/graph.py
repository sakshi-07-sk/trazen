"""Graph Nodes, Edges, and Path ORM Models."""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy import ForeignKey, Index, Integer, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from cryptotrace.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class GraphNodeModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Persisted node in an investigation graph."""

    __tablename__ = "graph_nodes"

    investigation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    node_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    node_type: Mapped[str] = mapped_column(String(50), nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    blockchain: Mapped[str] = mapped_column(String(50), nullable=False)
    chain_id: Mapped[str] = mapped_column(String(50), nullable=False)
    properties: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Relationship
    investigation: Mapped["InvestigationModel"] = relationship(  # noqa: F821
        "InvestigationModel",
        back_populates="nodes",
    )

    __table_args__ = (
        Index("idx_graph_node_inv_id", "investigation_id", "node_id", unique=True),
    )


class GraphEdgeModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Persisted directed relationship between graph nodes."""

    __tablename__ = "graph_edges"

    investigation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    target_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    edge_type: Mapped[str] = mapped_column(String(50), nullable=False)
    is_confirmed: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_heuristic: Mapped[bool] = mapped_column(default=False, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    asset_symbol: Mapped[str] = mapped_column(String(50), default="NATIVE", nullable=False)
    tx_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    evidence_reference: Mapped[str] = mapped_column(String(200), nullable=False)
    properties: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Relationship
    investigation: Mapped["InvestigationModel"] = relationship(  # noqa: F821
        "InvestigationModel",
        back_populates="edges",
    )

    __table_args__ = (
        Index("idx_graph_edge_lookup", "investigation_id", "source_id", "target_id"),
        Index("idx_graph_edge_tx", "tx_hash"),
    )


class InvestigationPathModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Traversed path through multi-hop forensic analysis."""

    __tablename__ = "investigation_paths"

    investigation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    path_nodes: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    hop_count: Mapped[int] = mapped_column(Integer, nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    summary_info: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    __table_args__ = (
        Index("idx_path_investigation_hops", "investigation_id", "hop_count"),
    )
