import hashlib
import time
import threading
from server.config import L1_TTL_SECONDS

class L1ExactCache:
    def __init__(self):
        self._store = {}
        self._lock = threading.Lock()

    def _key(self, query: str, intent: str, language: str = "en") -> str:
        raw = f"{query.strip().lower()}|{intent}|{language}"
        return hashlib.sha256(raw.encode()).hexdigest()

    async def get(self, query: str, intent: str, language: str = "en") -> dict | None:
        k = self._key(query, intent, language)
        with self._lock:
            entry = self._store.get(k)
            if entry and (time.time() - entry["ts"]) < L1_TTL_SECONDS:
                return entry["data"]
            if entry:
                del self._store[k]
        return None

    async def put(self, query: str, intent: str, data: dict, language: str = "en"):
        k = self._key(query, intent, language)
        with self._lock:
            self._store[k] = {"data": data, "ts": time.time()}

    async def clear(self):
        with self._lock:
            self._store.clear()

l1_cache = L1ExactCache()
