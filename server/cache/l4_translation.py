import hashlib
import time
import threading
from server.config import L4_TTL_SECONDS

class L4TranslationCache:
    def __init__(self):
        self._store = {}
        self._lock = threading.Lock()

    def _key(self, text: str, lang_pair: str) -> str:
        raw = f"{text}|{lang_pair}"
        return hashlib.sha256(raw.encode()).hexdigest()

    async def get(self, text: str, lang_pair: str) -> str | None:
        k = self._key(text, lang_pair)
        with self._lock:
            entry = self._store.get(k)
            if entry and (time.time() - entry["ts"]) < L4_TTL_SECONDS:
                return entry["translation"]
            if entry:
                del self._store[k]
        return None

    async def put(self, text: str, lang_pair: str, translation: str):
        k = self._key(text, lang_pair)
        with self._lock:
            self._store[k] = {"translation": translation, "ts": time.time()}

l4_cache = L4TranslationCache()
