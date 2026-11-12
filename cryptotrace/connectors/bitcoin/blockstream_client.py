"""Blockstream / Mempool REST API Client for Bitcoin."""

import hashlib
import json
from typing import Any, Dict, List
import httpx

from cryptotrace.core.exceptions import ProviderError, ProviderTimeoutError, RateLimitError
from cryptotrace.core.logging import logger
from cryptotrace.core.retry import AsyncRateLimiter, execute_with_retry


class BlockstreamClient:
    """Async client interacting with Blockstream / Mempool.space open Bitcoin API."""

    def __init__(
        self,
        base_url: str = "https://blockstream.info/api",
        timeout: float = 10.0,
        rate_limit_rps: float = 5.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.limiter = AsyncRateLimiter(requests_per_second=rate_limit_rps)

    async def _request(self, endpoint: str) -> Any:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        await self.limiter.acquire()

        async def _call():
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.get(url)
                    if resp.status_code == 429:
                        retry_after = float(resp.headers.get("Retry-After", 2.0))
                        raise RateLimitError("blockstream", retry_after=retry_after)
                    if resp.status_code == 404:
                        return None
                    resp.raise_for_status()
                    return resp.json()
            except httpx.TimeoutException:
                raise ProviderTimeoutError("blockstream", self.timeout)
            except (RateLimitError, ProviderTimeoutError):
                raise
            except Exception as e:
                raise ProviderError(
                    provider="blockstream",
                    message=f"Request to {url} failed: {e}",
                    details={"url": url},
                )

        return await execute_with_retry(_call, provider_name="blockstream")

    async def get_address(self, address: str) -> Dict[str, Any]:
        data = await self._request(f"/address/{address}")
        if data is None:
            return {
                "address": address,
                "chain_stats": {"funded_txo_count": 0, "funded_txo_sum": 0, "spent_txo_count": 0, "spent_txo_sum": 0, "tx_count": 0},
                "mempool_stats": {"funded_txo_count": 0, "funded_txo_sum": 0, "spent_txo_count": 0, "spent_txo_sum": 0, "tx_count": 0},
                "_raw_hash": hashlib.sha256(b"{}").hexdigest(),
                "_is_fixture": False,
            }
        data["_raw_hash"] = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        data["_is_fixture"] = False
        return data

    async def get_transaction(self, tx_hash: str) -> Dict[str, Any]:
        data = await self._request(f"/tx/{tx_hash}")
        if data is None:
            raise ProviderError("blockstream", f"Bitcoin tx {tx_hash} not found", status_code=404)
        data["_raw_hash"] = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        data["_is_fixture"] = False
        return data

    async def get_address_txs(self, address: str) -> List[Dict[str, Any]]:
        txs = await self._request(f"/address/{address}/txs") or []
        for tx in txs:
            tx["_raw_hash"] = hashlib.sha256(json.dumps(tx, sort_keys=True).encode()).hexdigest()
            tx["_is_fixture"] = False
        return txs

    async def get_block(self, block_hash: str) -> Dict[str, Any]:
        data = await self._request(f"/block/{block_hash}")
        if data is None:
            raise ProviderError("blockstream", f"Bitcoin block {block_hash} not found", status_code=404)
        data["_raw_hash"] = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        data["_is_fixture"] = False
        return data
