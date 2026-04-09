import hashlib
import numpy as np
from server.config import BM25_WEIGHT, COSINE_WEIGHT, TOP_K_FINAL, CONFIDENCE_THRESHOLD
from server.rag.vector_store import vector_store
from server.rag.bm25_store import bm25_store
from server.rag.embeddings import embed_single
from server.cache.l3_chunk import l3_cache

async def hybrid_retrieve(query: str, domains: list[str]) -> list[dict]:
    query_hash = hashlib.sha256(query.lower().encode()).hexdigest()[:16]
    for domain in domains:
        cached = await l3_cache.get(domain, query_hash)
        if cached:
            return cached
    query_embedding = await embed_single(query)
    all_results = {}
    for domain in domains:
        cosine_results = vector_store.search(domain, query_embedding)
        bm25_results = bm25_store.search(domain, query)
        if cosine_results:
            max_cosine = max(s for _, s in cosine_results) if cosine_results else 1.0
            for chunk, score in cosine_results:
                cid = chunk["id"]
                normalized = score / max(max_cosine, 1e-10)
                if cid not in all_results:
                    all_results[cid] = {"chunk": chunk, "cosine": 0, "bm25": 0}
                all_results[cid]["cosine"] = max(all_results[cid]["cosine"], normalized)
        if bm25_results:
            max_bm25 = max(s for _, s in bm25_results) if bm25_results else 1.0
            for chunk, score in bm25_results:
                cid = chunk["id"]
                normalized = score / max(max_bm25, 1e-10)
                if cid not in all_results:
                    all_results[cid] = {"chunk": chunk, "cosine": 0, "bm25": 0}
                all_results[cid]["bm25"] = max(all_results[cid]["bm25"], normalized)
    scored = []
    for cid, data in all_results.items():
        combined = COSINE_WEIGHT * data["cosine"] + BM25_WEIGHT * data["bm25"]
        if combined >= CONFIDENCE_THRESHOLD:
            scored.append({**data["chunk"], "score": combined})
    scored.sort(key=lambda x: x["score"], reverse=True)
    final = scored[:TOP_K_FINAL]
    if final:
        for domain in domains:
            await l3_cache.put(domain, query_hash, final)
    return final
