"""Investigation ORM Model."""

from typing import Any, Dict, List, Optional
from sqlalchemy import Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from cryptotrace.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class InvestigationModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Forensic investigation case tracking."""

    __tablename__ = "investigations"

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    blockchain: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    target_address: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    max_hops: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="created", nullable=False, index=True)
    total_transactions_ingested: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_nodes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_edges: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parameters: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    transactions: Mapped[List["TransactionModel"]] = relationship(  # noqa: F821
        "TransactionModel",
        back_populates="investigation",
        cascade="all, delete-orphan",
    )
    nodes: Mapped[List["GraphNodeModel"]] = relationship(  # noqa: F821
        "GraphNodeModel",
        back_populates="investigation",
        cascade="all, delete-orphan",
    )
    edges: Mapped[List["GraphEdgeModel"]] = relationship(  # noqa: F821
        "GraphEdgeModel",
        back_populates="investigation",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_investigation_blockchain_target", "blockchain", "target_address"),
    )
