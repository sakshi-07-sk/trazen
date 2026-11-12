"""Resilience helpers: bounded exponential backoff, rate limiting, and semaphore throttling."""

import asyncio
import random
import time
from typing import Any, Callable, Coroutine, Optional, TypeVar
from cryptotrace.core.exceptions import ProviderTimeoutError, RateLimitError
from cryptotrace.core.logging import logger

T = TypeVar("T")


class AsyncRateLimiter:
    """Token-bucket rate limiter for external provider calls."""

    def __init__(self, requests_per_second: float = 5.0, burst: int = 5) -> None:
        self.rate = requests_per_second
        self.capacity = burst
        self.tokens = burst
        self.last_updated = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire a token, pausing if exhausted."""
        async with self._lock:
            while True:
                now = time.monotonic()
                elapsed = now - self.last_updated
                self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
                self.last_updated = now

                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return

                sleep_time = (1.0 - self.tokens) / self.rate
                await asyncio.sleep(sleep_time)


async def execute_with_retry(
    operation: Callable[[], Coroutine[Any, Any, T]],
    provider_name: str,
    max_retries: int = 3,
    backoff_factor: float = 1.5,
    max_delay: float = 10.0,
) -> T:
    """Execute an async operation with bounded exponential backoff and jitter."""
    attempt = 0
    while True:
        try:
            return await operation()
        except (RateLimitError, ProviderTimeoutError, TimeoutError, asyncio.TimeoutError) as exc:
            attempt += 1
            if attempt > max_retries:
                logger.error(
                    f"Provider [{provider_name}] failed after {max_retries} retries: {exc}"
                )
                raise

            # Bounded exponential backoff with jitter
            base_delay = backoff_factor ** attempt
            jitter = random.uniform(0.1, 0.5)
            delay = min(base_delay + jitter, max_delay)

            logger.warning(
                f"Provider [{provider_name}] retry {attempt}/{max_retries} after {delay:.2f}s due to: {exc}"
            )
            await asyncio.sleep(delay)
        except Exception as exc:
            # Non-retryable error
            logger.error(f"Unrecoverable error from provider [{provider_name}]: {exc}")
            raise
