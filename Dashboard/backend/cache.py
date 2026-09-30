from __future__ import annotations

import os
import threading
import time
from typing import Any, Callable, Dict, Hashable, Tuple

DEFAULT_MAX_ENTRIES = 512


class TTLCache:
    def __init__(
        self,
        ttl: float,
        clock: Callable[[], float] = time.monotonic,
        max_entries: int = DEFAULT_MAX_ENTRIES,
    ) -> None:
        self.ttl = ttl
        self.clock = clock
        self.max_entries = max_entries
        self._data: Dict[Hashable, Tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get_or_load(self, key: Hashable, load: Callable[[], Any]) -> Any:
        if self.ttl <= 0:
            return load()
        with self._lock:
            hit = self._data.get(key)
            if hit and self.clock() - hit[0] < self.ttl:
                return hit[1]
        value = load()
        with self._lock:
            self._store_locked(key, value)
        return value

    def _store_locked(self, key: Hashable, value: Any) -> None:
        self._evict_expired_locked()
        # Remove antes de reinserir: se a chave já existia (ex.: duas cargas concorrentes
        # da mesma chave), isso a move para o fim, contando como a mais recente para a
        # eviction por `max_entries` — senão ela manteria a posição antiga do dict.
        self._data.pop(key, None)
        self._data[key] = (self.clock(), value)
        self._evict_oldest_locked()

    def _evict_expired_locked(self) -> None:
        now = self.clock()
        expired = [k for k, (t, _) in self._data.items() if now - t >= self.ttl]
        for k in expired:
            del self._data[k]

    def _evict_oldest_locked(self) -> None:
        while len(self._data) > self.max_entries:
            oldest_key = next(iter(self._data))
            del self._data[oldest_key]


query_cache = TTLCache(ttl=float(os.getenv("QUERY_CACHE_TTL_SECONDS", "3600")))
