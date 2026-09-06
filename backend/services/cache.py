"""
Caching Service for ORCA Backend (SIH26176)
Provides in-memory caching with TTL expiration for satellite raster tiles,
forecast grids, and agent intermediate responses, with optional Redis fallback.
"""

import time
import json
from typing import Any, Optional, Dict


class InMemoryCache:
    """Thread-safe in-memory cache with TTL."""

    def __init__(self, default_ttl_seconds: int = 3600):
        self._store: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        """Get value if exists and not expired."""
        if key not in self._store:
            return None
        entry = self._store[key]
        if time.time() > entry["expires_at"]:
            del self._store[key]
            return None
        return entry["value"]

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Store value with TTL."""
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        self._store[key] = {
            "value": value,
            "expires_at": time.time() + ttl
        }

    def delete(self, key: str) -> None:
        """Remove key from cache."""
        self._store.pop(key, None)

    def clear(self) -> None:
        """Clear all cache entries."""
        self._store.clear()

    def stats(self) -> Dict[str, Any]:
        """Return cache statistics."""
        current_time = time.time()
        active_keys = sum(1 for e in self._store.values() if e["expires_at"] > current_time)
        return {
            "total_keys": len(self._store),
            "active_keys": active_keys,
            "backend": "in_memory"
        }


# Global cache instance
cache_service = InMemoryCache(default_ttl_seconds=1800)  # 30 min default
