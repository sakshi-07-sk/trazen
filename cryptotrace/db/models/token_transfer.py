"""Token Transfer (ERC-20) ORM Model."""

from decimal import Decimal
from typing import Optional
from sqlalchemy import ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from cryptotrace.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class TokenTransferModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Normalized ERC-20 / Internal token transfers."""

    __tablename__ = "token_transfers"

    transaction_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    transaction_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    token_address: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    token_symbol: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    token_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    token_decimals: Mapped[int] = mapped_column(Integer, default=18, nullable=False)

    from_address: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    to_address: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    raw_value: Mapped[str] = mapped_column(String(78), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    log_index: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    block_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Relationships
    transaction: Mapped["TransactionModel"] = relationship(  # noqa: F821
        "TransactionModel",
        back_populates="token_transfers",
    )

    __table_args__ = (
        Index("idx_tokentx_parties", "from_address", "to_address"),
        Index("idx_tokentx_token_contract", "token_address", "token_symbol"),
    )
