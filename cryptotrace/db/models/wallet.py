"""Wallet ORM Model."""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy import Index, Integer, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from cryptotrace.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class WalletModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Normalized on-chain address profile."""

    __tablename__ = "wallets"

    address: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    blockchain: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    chain_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    node_type: Mapped[str] = mapped_column(String(50), default="wallet", nullable=False)
    balance_native: Mapped[Decimal] = mapped_column(Numeric(38, 18), default=Decimal("0"), nullable=False)
    total_received: Mapped[Decimal] = mapped_column(Numeric(38, 18), default=Decimal("0"), nullable=False)
    total_sent: Mapped[Decimal] = mapped_column(Numeric(38, 18), default=Decimal("0"), nullable=False)
    transaction_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    first_seen_timestamp: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    last_seen_timestamp: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tags: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    properties: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    __table_args__ = (
        Index("idx_wallet_unique_chain_address", "blockchain", "address", unique=True),
        Index("idx_wallet_chain_type", "blockchain", "node_type"),
    )
