"""Etherscan API and JSON-RPC Client for Ethereum."""

import hashlib
import json
from typing import Any, Dict, List, Optional
import httpx

from cryptotrace.core.exceptions import ProviderError, ProviderTimeoutError, RateLimitError
from cryptotrace.core.logging import logger
from cryptotrace.core.retry import AsyncRateLimiter, execute_with_retry


class EtherscanClient:
    """Async client interacting with Etherscan REST API and Ethereum JSON-RPC proxy."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.etherscan.io/api",
        timeout: float = 10.0,
        rate_limit_rps: float = 5.0,
    ) -> None:
        self.api_key = api_key or ""
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.limiter = AsyncRateLimiter(requests_per_second=rate_limit_rps)

    async def _query(self, params: Dict[str, Any]) -> Any:
        query_params = {**params}
        if self.api_key:
            query_params["apikey"] = self.api_key

        await self.limiter.acquire()

        async def _call():
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.get(self.base_url, params=query_params)
                    if resp.status_code == 429:
                        raise RateLimitError("etherscan", retry_after=1.0)
                    resp.raise_for_status()
                    payload = resp.json()
                    if payload.get("status") == "0" and payload.get("message") == "NOTOK":
                        msg = payload.get("result", "")
                        if "rate limit" in str(msg).lower():
                            raise RateLimitError("etherscan", retry_after=1.0)
                        raise ProviderError("etherscan", f"Etherscan error: {msg}")
                    return payload
            except httpx.TimeoutException:
                raise ProviderTimeoutError("etherscan", self.timeout)
            except (RateLimitError, ProviderTimeoutError, ProviderError):
                raise
            except Exception as e:
                raise ProviderError("etherscan", f"Failed query {params}: {e}")

        return await execute_with_retry(_call, provider_name="etherscan")

    async def get_balance(self, address: str) -> str:
        data = await self._query({
            "module": "account",
            "action": "balance",
            "address": address,
            "tag": "latest",
        })
        return str(data.get("result", "0"))

    async def get_tx_list(self, address: str, offset: int = 50) -> List[Dict[str, Any]]:
        data = await self._query({
            "module": "account",
            "action": "txlist",
            "address": address,
            "startblock": 0,
            "endblock": 99999999,
            "page": 1,
            "offset": offset,
            "sort": "desc",
        })
        return data.get("result", [])

    async def get_erc20_transfers(self, address: str, offset: int = 50) -> List[Dict[str, Any]]:
        data = await self._query({
            "module": "account",
            "action": "tokentx",
            "address": address,
            "page": 1,
            "offset": offset,
            "sort": "desc",
        })
        return data.get("result", [])

    async def get_transaction_by_hash(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        data = await self._query({
            "module": "proxy",
            "action": "eth_getTransactionByHash",
            "txhash": tx_hash,
        })
        return data.get("result")
