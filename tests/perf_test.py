import asyncio
import time
import uuid
import os
from server.pipeline.language import detect_language
from server.pipeline.intent import classify_intent
from server.pipeline.session import SessionState, session_manager
from server.app import _try_extract_name, _process_query, load_knowledge
from server.cache.l1_exact import l1_cache
from server.cache.l2_semantic import l2_cache
from server.rag.embeddings import embed_single, _get_model as get_embed_model

async def run_perf_test():
    print("--- Performance Analysis ---")
    
    # 1. Language Detection
    start = time.perf_counter()
    detect_language("What are the courses offered?", "en")
    ld_lat = (time.perf_counter() - start) * 1000
    print(f"Language detection latency: {ld_lat:.2f} ms")
    
    # 2. Intent Classification
    start = time.perf_counter()
    classify_intent("What is the fee for CSE?")
    ic_lat = (time.perf_counter() - start) * 1000
    print(f"Intent classification latency: {ic_lat:.2f} ms")
    
    # 3. Name Extraction
    session = SessionState(session_id="test")
    start = time.perf_counter()
    _try_extract_name("My name is Arjun", session)
    ne_lat = (time.perf_counter() - start) * 1000
    print(f"Name extraction latency: {ne_lat:.2f} ms")
    
    # 4. L1 Cache Lookup
    start = time.perf_counter()
    await l1_cache.get("test query", "general", "en")
    l1_lat = (time.perf_counter() - start) * 1000
    print(f"L1 cache lookup latency: {l1_lat:.2f} ms")
    
    # 5. Sentence Transformer Startup
    start = time.perf_counter()
    get_embed_model()
    st_start = (time.perf_counter() - start) * 1000
    print(f"Sentence Transformer load time: {st_start:.2f} ms")
    
    # 6. L2 Embedding + Similarity
    start = time.perf_counter()
    emb = await embed_single("test query")
    await l2_cache.get(emb, "en")
    l2_lat = (time.perf_counter() - start) * 1000
    print(f"L2 embedding + similarity latency: {l2_lat:.2f} ms")

if __name__ == "__main__":
    asyncio.run(run_perf_test())
