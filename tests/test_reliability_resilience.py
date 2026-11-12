"""Tests for Reliability, Retries, Rate-Limiting, and Cache Management."""

import asyncio
import time
import pytest
from cryptotrace.core.cache import AsyncCache
from cryptotrace.core.exceptions import ProviderTimeoutError, RateLimitError
from cryptotrace.core.retry import AsyncRateLimiter, execute_with_retry


@pytest.mark.asyncio
async def test_cache_set_get_and_ttl():
    cache = AsyncCache(ttl_seconds=1, max_items=5)
    await cache.set("key1", {"data": "test_payload"}, ttl=1)

    val = await cache.get("key1")
    assert val == {"data": "test_payload"}

    # Wait for expiration
    await asyncio.sleep(1.1)
    expired_val = await cache.get("key1")
    assert expired_val is None


@pytest.mark.asyncio
async def test_cache_eviction_on_max_items():
    cache = AsyncCache(ttl_seconds=60, max_items=2)
    await cache.set("k1", "v1")
    await asyncio.sleep(0.01)
    await cache.set("k2", "v2")
    await asyncio.sleep(0.01)
    # Adding 3rd key should evict oldest (k1)
    await cache.set("k3", "v3")

    assert await cache.get("k1") is None
    assert await cache.get("k2") == "v2"
    assert await cache.get("k3") == "v3"


@pytest.mark.asyncio
async def test_retry_with_bounded_backoff_success():
    attempts = 0

    async def flaky_call():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ProviderTimeoutError(provider="test_prov", timeout_seconds=1.0)
        return "success"

    result = await execute_with_retry(
        flaky_call,
        provider_name="test_prov",
        max_retries=3,
        backoff_factor=1.1,
        max_delay=0.5,
    )
    assert result == "success"
    assert attempts == 3


@pytest.mark.asyncio
async def test_retry_exceeds_max_attempts_raises():
    async def always_fails():
        raise RateLimitError(provider="test_prov", retry_after=0.1)

    with pytest.raises(RateLimitError):
        await execute_with_retry(
            always_fails,
            provider_name="test_prov",
            max_retries=2,
            backoff_factor=1.0,
            max_delay=0.1,
        )


@pytest.mark.asyncio
async def test_rate_limiter_throttles():
    limiter = AsyncRateLimiter(requests_per_second=10.0, burst=2)
    start_t = time.monotonic()
    # Acquire 3 tokens (burst is 2, 3rd must wait)
    for _ in range(3):
        await limiter.acquire()
    elapsed = time.monotonic() - start_t
    assert elapsed >= 0.05
