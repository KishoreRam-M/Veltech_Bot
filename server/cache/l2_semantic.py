import time
import asyncio
import numpy as np
from server.config import L2_TTL_SECONDS, L2_SIMILARITY_THRESHOLD

class L2SemanticCache:
    def __init__(self):
        self._embeddings = []
        self._responses = []
        self._timestamps = []
        self._lock = asyncio.Lock()

    async def get(self, query_embedding: np.ndarray) -> dict | None:
        async with self._lock:
            if not self._embeddings:
                return None
            now = time.time()
            valid = []
            for i, (emb, resp, ts) in enumerate(zip(self._embeddings, self._responses, self._timestamps)):
                if (now - ts) < L2_TTL_SECONDS:
                    valid.append((emb, resp, ts, i))
            if not valid:
                self._embeddings.clear()
                self._responses.clear()
                self._timestamps.clear()
                return None
            mat = np.array([v[0] for v in valid])
            qn = query_embedding / (np.linalg.norm(query_embedding) + 1e-10)
            mn = mat / (np.linalg.norm(mat, axis=1, keepdims=True) + 1e-10)
            sims = mn @ qn
            best_idx = int(np.argmax(sims))
            if sims[best_idx] >= L2_SIMILARITY_THRESHOLD:
                return valid[best_idx][1]
        return None

    async def put(self, query_embedding: np.ndarray, data: dict):
        async with self._lock:
            self._embeddings.append(query_embedding.tolist())
            self._responses.append(data)
            self._timestamps.append(time.time())

    async def clear(self):
        async with self._lock:
            self._embeddings.clear()
            self._responses.clear()
            self._timestamps.clear()

l2_cache = L2SemanticCache()
