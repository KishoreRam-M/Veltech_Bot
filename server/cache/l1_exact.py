import hashlib
import time
import asyncio
from server.config import L1_TTL_SECONDS

class L1ExactCache:
    def __init__(self):
        self._store = {}
        self._lock = asyncio.Lock()

    def _key(self, query: str, intent: str) -> str:
        raw = f"{query.strip().lower()}|{intent}"
        return hashlib.sha256(raw.encode()).hexdigest()

    async def get(self, query: str, intent: str) -> dict | None:
        k = self._key(query, intent)
        async with self._lock:
            entry = self._store.get(k)
            if entry and (time.time() - entry["ts"]) < L1_TTL_SECONDS:
                return entry["data"]
            if entry:
                del self._store[k]
        return None

    async def put(self, query: str, intent: str, data: dict):
        k = self._key(query, intent)
        async with self._lock:
            self._store[k] = {"data": data, "ts": time.time()}

    async def clear(self):
        async with self._lock:
            self._store.clear()

l1_cache = L1ExactCache()
