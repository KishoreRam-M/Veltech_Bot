import os
import pickle
from server.config import KNOWLEDGE_DIR, DOMAINS
from server.rag.vector_store import vector_store
from server.rag.bm25_store import bm25_store

async def load_knowledge():
    for domain_name, domain_cfg in DOMAINS.items():
        emb_path = os.path.join(KNOWLEDGE_DIR, f"{domain_name}.npy")
        meta_path = os.path.join(KNOWLEDGE_DIR, f"{domain_name}_meta.pkl")

        if os.path.exists(emb_path) and os.path.exists(meta_path):
            vector_store.load_index(domain_name, emb_path, meta_path)
            with open(meta_path, "rb") as f:
                chunks = pickle.load(f)
            bm25_store.build_index(domain_name, chunks)
            print(f"[KB] Loaded {domain_name}: {len(chunks)} chunks (FAISS)")
        else:
            print(f"[KB] Missing index for '{domain_name}'. Run: python indexer.py")

    print(f"[KB] Knowledge base ready: {len(vector_store.domains)} domains")
