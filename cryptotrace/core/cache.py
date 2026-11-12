"""Asynchronous In-Memory Cache with TTL and Max-Key Eviction."""

import asyncio
import time
from typing import Any, Dict, Optional, Tuple


class AsyncCache:
    """Thread-safe async TTL cache for blockchain lookups and graph representations."""

    def __init__(self, ttl_seconds: int = 300, max_items: int = 5000) -> None:
        self.ttl = ttl_seconds
        self.max_items = max_items
        self._store: Dict[str, Tuple[float, Any]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """Retrieve value by key if not expired."""
        async with self._lock:
            if key not in self._store:
                return None
            expire_at, value = self._store[key]
            if time.time() > expire_at:
                del self._store[key]
                return None
            return value

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store key-value with TTL expiration."""
        expiry = time.time() + (ttl if ttl is not None else self.ttl)
        async with self._lock:
            if len(self._store) >= self.max_items and key not in self._store:
                # Evict oldest entry
                oldest_key = min(self._store.keys(), key=lambda k: self._store[k][0])
                del self._store[oldest_key]
            self._store[key] = (expiry, value)

    async def delete(self, key: str) -> bool:
        """Remove key from cache."""
        async with self._lock:
            if key in self._store:
                del self._store[key]
                return True
            return False

    async def clear(self) -> None:
        """Clear all entries."""
        async with self._lock:
            self._store.clear()

    async def size(self) -> int:
        """Return count of active items in cache."""
        async with self._lock:
            now = time.time()
            return sum(1 for exp, _ in self._store.values() if exp > now)


# Global singleton instance
default_cache = AsyncCache()
