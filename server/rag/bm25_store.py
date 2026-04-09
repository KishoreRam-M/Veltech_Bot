from rank_bm25 import BM25Okapi
from server.config import TOP_K_RETRIEVAL

class BM25Store:
    def __init__(self):
        self._indices = {}
        self._chunks = {}

    def build_index(self, domain: str, chunks: list[dict]):
        tokenized = [chunk["text"].lower().split() for chunk in chunks]
        self._indices[domain] = BM25Okapi(tokenized)
        self._chunks[domain] = chunks

    def search(self, domain: str, query: str, top_k: int = TOP_K_RETRIEVAL) -> list[tuple[dict, float]]:
        if domain not in self._indices:
            return []
        bm25 = self._indices[domain]
        tokens = query.lower().split()
        scores = bm25.get_scores(tokens)
        top_indices = scores.argsort()[-top_k:][::-1]
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append((self._chunks[domain][idx], float(scores[idx])))
        return results

    def has_domain(self, domain: str) -> bool:
        return domain in self._indices

bm25_store = BM25Store()
