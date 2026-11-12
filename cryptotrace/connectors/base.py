"""Base Abstract Blockchain Adapter Interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from cryptotrace.schemas.common import BlockchainType


class BaseBlockchainAdapter(ABC):
    """Abstract interface defining required capabilities for blockchain data providers."""

    def __init__(self, provider_name: str, is_fixture: bool = False) -> None:
        self.provider_name = provider_name
        self.is_fixture = is_fixture

    @property
    @abstractmethod
    def blockchain(self) -> BlockchainType:
        """Returns the blockchain ecosystem name."""
        pass

    @abstractmethod
    def validate_address(self, address: str) -> bool:
        """Check if address adheres to chain syntax standards."""
        pass

    @abstractmethod
    def validate_tx_hash(self, tx_hash: str) -> bool:
        """Check if transaction hash adheres to chain format."""
        pass

    @abstractmethod
    async def get_address_info(self, address: str) -> Dict[str, Any]:
        """Fetch balance, transaction counts, and metadata for an address."""
        pass

    @abstractmethod
    async def get_transaction(self, tx_hash: str) -> Dict[str, Any]:
        """Fetch raw transaction payload by hash."""
        pass

    @abstractmethod
    async def get_transactions_for_address(
        self, address: str, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Fetch raw transaction history for an address."""
        pass

    @abstractmethod
    async def get_block(self, block_identifier: Any) -> Dict[str, Any]:
        """Fetch block header and transaction lists."""
        pass
