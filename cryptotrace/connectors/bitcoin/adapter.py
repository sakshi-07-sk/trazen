"""Bitcoin Blockchain Adapter."""

from typing import Any, Dict, List, Optional
from cryptotrace.config import get_settings
from cryptotrace.connectors.base import BaseBlockchainAdapter
from cryptotrace.connectors.bitcoin.blockstream_client import BlockstreamClient
from cryptotrace.connectors.fixtures.mock_provider import BitcoinMockAdapter
from cryptotrace.core.cache import default_cache
from cryptotrace.core.exceptions import InvalidAddressError, InvalidHashError
from cryptotrace.core.logging import logger
from cryptotrace.schemas.common import BlockchainType


class BitcoinAdapter(BaseBlockchainAdapter):
    """Production-grade Bitcoin adapter with caching, rate limiting, and fixture fallback."""

    def __init__(
        self,
        api_url: Optional[str] = None,
        use_fixtures: Optional[bool] = None,
    ) -> None:
        settings = get_settings()
        self.use_fixtures = (
            use_fixtures if use_fixtures is not None else settings.DEMO_FIXTURE_MODE
        )
        self.mock_adapter = BitcoinMockAdapter()
        self.client = BlockstreamClient(
            base_url=api_url or settings.BLOCKSTREAM_API_URL,
            timeout=settings.PROVIDER_TIMEOUT_SECONDS,
            rate_limit_rps=settings.PROVIDER_RATE_LIMIT_RPS,
        )
        super().__init__(
            provider_name="fixture_provider" if self.use_fixtures else "blockstream",
            is_fixture=self.use_fixtures,
        )

    @property
    def blockchain(self) -> BlockchainType:
        return BlockchainType.BITCOIN

    def validate_address(self, address: str) -> bool:
        return self.mock_adapter.validate_address(address)

    def validate_tx_hash(self, tx_hash: str) -> bool:
        return self.mock_adapter.validate_tx_hash(tx_hash)

    async def get_address_info(self, address: str) -> Dict[str, Any]:
        if not self.validate_address(address):
            raise InvalidAddressError(address, "bitcoin")

        cache_key = f"btc:address:{address}"
        cached = await default_cache.get(cache_key)
        if cached:
            return cached

        if self.use_fixtures:
            result = await self.mock_adapter.get_address_info(address)
        else:
            try:
                result = await self.client.get_address(address)
            except Exception as e:
                logger.warning(f"Live Bitcoin lookup failed, falling back to fixture: {e}")
                result = await self.mock_adapter.get_address_info(address)

        await default_cache.set(cache_key, result, ttl=180)
        return result

    async def get_transaction(self, tx_hash: str) -> Dict[str, Any]:
        if not self.validate_tx_hash(tx_hash):
            raise InvalidHashError(tx_hash, "bitcoin")

        cache_key = f"btc:tx:{tx_hash}"
        cached = await default_cache.get(cache_key)
        if cached:
            return cached

        if self.use_fixtures:
            result = await self.mock_adapter.get_transaction(tx_hash)
        else:
            try:
                result = await self.client.get_transaction(tx_hash)
            except Exception as e:
                logger.warning(f"Live Bitcoin tx query failed, falling back to fixture: {e}")
                result = await self.mock_adapter.get_transaction(tx_hash)

        await default_cache.set(cache_key, result, ttl=300)
        return result

    async def get_transactions_for_address(
        self, address: str, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        if not self.validate_address(address):
            raise InvalidAddressError(address, "bitcoin")

        if self.use_fixtures:
            return await self.mock_adapter.get_transactions_for_address(address, limit, offset)

        try:
            txs = await self.client.get_address_txs(address)
            return txs[offset : offset + limit]
        except Exception as e:
            logger.warning(f"Live Bitcoin txs query failed, falling back to fixture: {e}")
            return await self.mock_adapter.get_transactions_for_address(address, limit, offset)

    async def get_block(self, block_identifier: Any) -> Dict[str, Any]:
        if self.use_fixtures:
            return await self.mock_adapter.get_block(block_identifier)

        try:
            return await self.client.get_block(str(block_identifier))
        except Exception as e:
            logger.warning(f"Live Bitcoin block query failed, falling back to fixture: {e}")
            return await self.mock_adapter.get_block(block_identifier)
