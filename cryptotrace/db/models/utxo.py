"""Bitcoin UTXO and Transaction Outputs ORM Model."""

from decimal import Decimal
from typing import Optional
from sqlalchemy import ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from cryptotrace.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class UTXOModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Bitcoin Unspent Transaction Output record."""

    __tablename__ = "utxos"

    transaction_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tx_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    vout: Mapped[int] = mapped_column(Integer, nullable=False)
    address: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    amount_sats: Mapped[int] = mapped_column(Integer, nullable=False)
    amount_btc: Mapped[Decimal] = mapped_column(Numeric(38, 8), nullable=False)
    script_pubkey: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    script_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_spent: Mapped[bool] = mapped_column(default=False, nullable=False, index=True)
    spending_tx_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    prev_tx_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    # Relationships
    transaction: Mapped["TransactionModel"] = relationship(  # noqa: F821
        "TransactionModel",
        back_populates="utxos",
    )

    __table_args__ = (
        Index("idx_utxo_tx_vout", "tx_hash", "vout", unique=True),
        Index("idx_utxo_address_spent", "address", "is_spent"),
    )
