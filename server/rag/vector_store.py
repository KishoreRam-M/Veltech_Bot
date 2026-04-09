import os
import pickle
import numpy as np
import faiss
from server.config import TOP_K_RETRIEVAL, FAISS_THREADS

faiss.omp_set_num_threads(FAISS_THREADS)

class VectorStore:
    def __init__(self):
        self._indices = {}
        self._chunks = {}

    def load_index(self, domain: str, embeddings_path: str, meta_path: str):
        faiss_path = embeddings_path.replace(".npy", ".faiss")
        with open(meta_path, "rb") as f:
            self._chunks[domain] = pickle.load(f)
        if os.path.exists(faiss_path):
            self._indices[domain] = faiss.read_index(faiss_path)
        else:
            embeddings = np.load(embeddings_path).astype(np.float32)
            dim = embeddings.shape[1]
            index = faiss.IndexFlatIP(dim)
            index.add(embeddings)
            self._indices[domain] = index
            faiss.write_index(index, faiss_path)
            print(f"[FAISS] Built and cached index for {domain}")

    def search(self, domain: str, query_embedding: np.ndarray, top_k: int = TOP_K_RETRIEVAL) -> list[tuple[dict, float]]:
        if domain not in self._indices:
            return []
        qe = query_embedding.reshape(1, -1).astype(np.float32)
        top_k = min(top_k, self._indices[domain].ntotal)
        if top_k == 0:
            return []
        scores, indices = self._indices[domain].search(qe, top_k)
        results = []
        for i in range(top_k):
            idx = int(indices[0][i])
            if idx >= 0 and idx < len(self._chunks[domain]):
                results.append((self._chunks[domain][idx], float(scores[0][i])))
        return results

    def has_domain(self, domain: str) -> bool:
        return domain in self._indices

    @property
    def domains(self) -> list[str]:
        return list(self._indices.keys())

vector_store = VectorStore()
