import hashlib
import time
import threading
from server.config import L3_TTL_SECONDS

class L3ChunkCache:
    def __init__(self):
        self._store = {}
        self._lock = threading.Lock()

    def _key(self, domain: str, query_hash: str) -> str:
        return f"{domain}|{query_hash}"

    async def get(self, domain: str, query_hash: str) -> list | None:
        k = self._key(domain, query_hash)
        with self._lock:
            entry = self._store.get(k)
            if entry and (time.time() - entry["ts"]) < L3_TTL_SECONDS:
                return entry["chunks"]
            if entry:
                del self._store[k]
        return None

    async def put(self, domain: str, query_hash: str, chunks: list):
        k = self._key(domain, query_hash)
        with self._lock:
            self._store[k] = {"chunks": chunks, "ts": time.time()}

l3_cache = L3ChunkCache()
