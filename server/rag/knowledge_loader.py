import os
from server.config import DOMAINS
from server.rag.vector_store import vector_store
from server.rag.bm25_store import bm25_store

async def load_knowledge():
    vector_store.init_db()
    for domain_name, domain_cfg in DOMAINS.items():
        if vector_store.has_domain(domain_name):
            chunks = vector_store.get_chunks_for_domain(domain_name)
            if chunks:
                bm25_store.build_index(domain_name, chunks)
                print(f"[KB] Loaded {domain_name}: {len(chunks)} chunks (LanceDB + BM25)")
            else:
                print(f"[KB] Domain {domain_name} found but no chunks loaded.")
        else:
            print(f"[KB] Missing LanceDB index for '{domain_name}'. Run: python indexer.py")

    print(f"[KB] Knowledge base ready: {len(vector_store.domains)} domains")
