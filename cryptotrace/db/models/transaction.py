"""Canonical Transaction ORM Model."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy import DateTime, ForeignKey, Index, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from cryptotrace.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class TransactionModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Canonical transaction model across all supported blockchains."""

    __tablename__ = "transactions"

    investigation_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("investigations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    chain_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    blockchain: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    tx_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    block_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    block_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    sender_references: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    recipient_references: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    asset_symbol: Mapped[str] = mapped_column(String(50), default="NATIVE", nullable=False)
    contract_address: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    fee: Mapped[Decimal] = mapped_column(Numeric(38, 18), default=Decimal("0"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="confirmed", nullable=False)
    confirmations: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Ethereum Specific
    from_address: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    to_address: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    gas_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    gas_price_gwei: Mapped[Optional[Decimal]] = mapped_column(Numeric(38, 9), nullable=True)
    nonce: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    input_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Bitcoin Specific
    vsize: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    locktime: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Provenance and raw payload
    raw_payload_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    provider_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_fixture: Mapped[bool] = mapped_column(default=False, nullable=False)
    raw_payload: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    investigation: Mapped[Optional["InvestigationModel"]] = relationship(  # noqa: F821
        "InvestigationModel",
        back_populates="transactions",
    )
    utxos: Mapped[List["UTXOModel"]] = relationship(  # noqa: F821
        "UTXOModel",
        back_populates="transaction",
        cascade="all, delete-orphan",
    )
    token_transfers: Mapped[List["TokenTransferModel"]] = relationship(  # noqa: F821
        "TokenTransferModel",
        back_populates="transaction",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_tx_unique_chain_hash", "blockchain", "tx_hash", unique=True),
        Index("idx_tx_block_timestamp", "blockchain", "block_number", "timestamp"),
        Index("idx_tx_eth_addresses", "from_address", "to_address"),
    )
