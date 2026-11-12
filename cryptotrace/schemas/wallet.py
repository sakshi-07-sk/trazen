"""Wallet and address profile schemas."""

from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field
from cryptotrace.schemas.common import BlockchainType, NodeType
from cryptotrace.schemas.provenance import DataSourceProvenance


class WalletProfile(BaseModel):
    """Forensic wallet profile."""

    address: str = Field(..., description="Public blockchain address")
    blockchain: BlockchainType = Field(..., description="Blockchain name")
    chain_id: str = Field(..., description="Chain identifier")
    node_type: NodeType = Field(default=NodeType.WALLET, description="Entity type classification")
    balance_native: Decimal = Field(default=Decimal("0"), description="Current native balance (BTC or ETH)")
    total_received: Decimal = Field(default=Decimal("0"), description="Historical received volume")
    total_sent: Decimal = Field(default=Decimal("0"), description="Historical sent volume")
    transaction_count: int = Field(default=0, ge=0, description="Total confirmed transactions")
    first_seen_timestamp: Optional[int] = Field(None, description="Unix timestamp of earliest transaction")
    last_seen_timestamp: Optional[int] = Field(None, description="Unix timestamp of latest transaction")
    tags: List[str] = Field(default_factory=list, description="Forensic tags (e.g. whale, exchange, mixer)")
    provenance: Optional[DataSourceProvenance] = Field(None, description="Provenance of address lookup")


class WalletSummary(BaseModel):
    """Lightweight wallet overview."""

    address: str
    blockchain: BlockchainType
    balance: Decimal
    tx_count: int
    is_contract: bool = False
