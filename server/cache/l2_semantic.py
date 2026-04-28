import time
import threading
import numpy as np
import asyncio
from server.config import L2_TTL_SECONDS, L2_SIMILARITY_THRESHOLD

# Maximum number of cached embeddings. Prevents unbounded RAM growth.
# Each slot ≈ 384 floats (1.5 KB) + response string. 500 slots ≈ <2 MB overhead.
_L2_MAX_SIZE = 500


class L2SemanticCache:
    def __init__(self):
        self._embeddings: list = []
        self._responses: list = []
        self._timestamps: list = []
        self._languages: list = []
        self._lock = threading.Lock()
        self._pending_tasks = {}
        self._pending_lock = threading.Lock()

    async def get(self, query_embedding: np.ndarray, language: str = "en") -> dict | None:
        with self._lock:
            if not self._embeddings:
                return None
            now = time.time()
            valid = []
            for emb, resp, ts, lang in zip(
                self._embeddings, self._responses, self._timestamps, self._languages
            ):
                if (now - ts) < L2_TTL_SECONDS and lang == language:
                    valid.append((emb, resp))
            if not valid:
                return None
            mat = np.array([v[0] for v in valid])
            qn = query_embedding / (np.linalg.norm(query_embedding) + 1e-10)
            mn = mat / (np.linalg.norm(mat, axis=1, keepdims=True) + 1e-10)
            sims = mn @ qn
            best_idx = int(np.argmax(sims))
            if sims[best_idx] >= L2_SIMILARITY_THRESHOLD:
                return valid[best_idx][1]
        return None

    async def put(self, query_embedding: np.ndarray, data: dict, language: str = "en"):
        with self._lock:
            # FIFO eviction when cap is reached — oldest entry is always index 0
            if len(self._embeddings) >= _L2_MAX_SIZE:
                self._embeddings.pop(0)
                self._responses.pop(0)
                self._timestamps.pop(0)
                self._languages.pop(0)
            self._embeddings.append(query_embedding.tolist())
            self._responses.append(data)
            self._timestamps.append(time.time())
            self._languages.append(language)

    async def clear(self):
        with self._lock:
            self._embeddings.clear()
            self._responses.clear()
            self._timestamps.clear()
            self._languages.clear()


l2_cache = L2SemanticCache()
