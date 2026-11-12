"""Ethereum Token Transfer Schemas (ERC-20, internal calls)."""

from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class TokenTransfer(BaseModel):
    """Normalized token transfer event (ERC-20 / internal trace)."""

    token_address: str = Field(..., description="Smart contract address")
    token_symbol: str = Field(..., description="Token ticker symbol, e.g. USDT, USDC, LINK")
    token_name: Optional[str] = Field(None, description="Full token name")
    token_decimals: int = Field(default=18, ge=0, le=36, description="Token decimal precision")
    from_address: str = Field(..., description="Transfer sender address")
    to_address: str = Field(..., description="Transfer recipient address")
    raw_value: str = Field(..., description="Raw integer token amount as string to preserve full precision")
    amount: Decimal = Field(..., description="Human-readable Decimal amount adjusted for token decimals")
    log_index: Optional[int] = Field(None, description="Log index within the transaction receipt")
    transaction_hash: str = Field(..., description="Parent transaction hash")
    block_number: int = Field(..., description="Block height of the transfer")

    @field_validator("amount", mode="before")
    @classmethod
    def validate_amount(cls, val):
        if isinstance(val, (int, float, str)):
            return Decimal(str(val))
        return val
