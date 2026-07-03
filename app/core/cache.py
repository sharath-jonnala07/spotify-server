import time
import threading
from typing import Any, Dict, Optional

class InMemoryCache:
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._cache:
                return None
            item = self._cache[key]
            if time.time() > item["expire_at"]:
                del self._cache[key]
                return None
            return item["value"]

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        with self._lock:
            self._cache[key] = {
                "value": value,
                "expire_at": time.time() + ttl_seconds
            }

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

# Global cache instance
cache = InMemoryCache()
