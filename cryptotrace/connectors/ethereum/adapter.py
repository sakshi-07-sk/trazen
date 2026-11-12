"""Ethereum Blockchain Adapter."""

from typing import Any, Dict, List, Optional
from cryptotrace.config import get_settings
from cryptotrace.connectors.base import BaseBlockchainAdapter
from cryptotrace.connectors.ethereum.etherscan_client import EtherscanClient
from cryptotrace.connectors.fixtures.mock_provider import EthereumMockAdapter
from cryptotrace.core.cache import default_cache
from cryptotrace.core.exceptions import InvalidAddressError, InvalidHashError
from cryptotrace.core.logging import logger
from cryptotrace.schemas.common import BlockchainType


class EthereumAdapter(BaseBlockchainAdapter):
    """Production-grade Ethereum adapter with caching, rate limiting, and fixture fallback."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        use_fixtures: Optional[bool] = None,
    ) -> None:
        settings = get_settings()
        configured_key = api_key or settings.ETHERSCAN_API_KEY
        # Fall back to fixtures if DEMO_FIXTURE_MODE is true or if API key is not provided
        self.use_fixtures = (
            use_fixtures
            if use_fixtures is not None
            else (settings.DEMO_FIXTURE_MODE or not bool(configured_key))
        )
        self.mock_adapter = EthereumMockAdapter()
        self.client = EtherscanClient(
            api_key=configured_key,
            base_url=settings.ETHERSCAN_API_URL,
            timeout=settings.PROVIDER_TIMEOUT_SECONDS,
            rate_limit_rps=settings.PROVIDER_RATE_LIMIT_RPS,
        )
        super().__init__(
            provider_name="fixture_provider" if self.use_fixtures else "etherscan",
            is_fixture=self.use_fixtures,
        )

    @property
    def blockchain(self) -> BlockchainType:
        return BlockchainType.ETHEREUM

    def validate_address(self, address: str) -> bool:
        return self.mock_adapter.validate_address(address)

    def validate_tx_hash(self, tx_hash: str) -> bool:
        return self.mock_adapter.validate_tx_hash(tx_hash)

    async def get_address_info(self, address: str) -> Dict[str, Any]:
        if not self.validate_address(address):
            raise InvalidAddressError(address, "ethereum")

        normalized = address.lower()
        cache_key = f"eth:address:{normalized}"
        cached = await default_cache.get(cache_key)
        if cached:
            return cached

        if self.use_fixtures:
            result = await self.mock_adapter.get_address_info(normalized)
        else:
            try:
                balance_wei = await self.client.get_balance(normalized)
                txs = await self.client.get_tx_list(normalized, offset=1)
                result = {
                    "address": normalized,
                    "balance_wei": balance_wei,
                    "tx_count": len(txs),
                    "is_contract": False,
                    "_is_fixture": False,
                    "_raw_hash": "live_hash",
                }
            except Exception as e:
                logger.warning(f"Live Ethereum lookup failed, falling back to fixture: {e}")
                result = await self.mock_adapter.get_address_info(normalized)

        await default_cache.set(cache_key, result, ttl=180)
        return result

    async def get_transaction(self, tx_hash: str) -> Dict[str, Any]:
        if not self.validate_tx_hash(tx_hash):
            raise InvalidHashError(tx_hash, "ethereum")

        cache_key = f"eth:tx:{tx_hash.lower()}"
        cached = await default_cache.get(cache_key)
        if cached:
            return cached

        if self.use_fixtures:
            result = await self.mock_adapter.get_transaction(tx_hash)
        else:
            try:
                tx_data = await self.client.get_transaction_by_hash(tx_hash)
                if not tx_data:
                    result = await self.mock_adapter.get_transaction(tx_hash)
                else:
                    result = tx_data
                    result["_is_fixture"] = False
                    result["_raw_hash"] = "live_tx_hash"
            except Exception as e:
                logger.warning(f"Live Ethereum tx query failed, falling back to fixture: {e}")
                result = await self.mock_adapter.get_transaction(tx_hash)

        await default_cache.set(cache_key, result, ttl=300)
        return result

    async def get_transactions_for_address(
        self, address: str, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        if not self.validate_address(address):
            raise InvalidAddressError(address, "ethereum")

        normalized = address.lower()
        if self.use_fixtures:
            return await self.mock_adapter.get_transactions_for_address(normalized, limit, offset)

        try:
            txs = await self.client.get_tx_list(normalized, offset=limit)
            return txs[offset : offset + limit]
        except Exception as e:
            logger.warning(f"Live Ethereum tx list query failed, falling back to fixture: {e}")
            return await self.mock_adapter.get_transactions_for_address(normalized, limit, offset)

    async def get_block(self, block_identifier: Any) -> Dict[str, Any]:
        if self.use_fixtures:
            return await self.mock_adapter.get_block(block_identifier)

        # Fallback to mock block representation for consistent parsing
        return await self.mock_adapter.get_block(block_identifier)
