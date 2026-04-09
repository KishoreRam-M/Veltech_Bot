import intel_setup

import os
import json
import pickle
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from server.config import DOMAINS, KNOWLEDGE_DIR, EMBEDDING_MODEL, MODEL_CACHE_DIR, EMBED_BATCH_SIZE

def run_indexer():
    os.makedirs(MODEL_CACHE_DIR, exist_ok=True)
    print(f"[INDEXER] Loading model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(
        EMBEDDING_MODEL,
        device="cpu",
        cache_folder=MODEL_CACHE_DIR,
    )

    for domain_name, cfg in DOMAINS.items():
        filepath = os.path.join(KNOWLEDGE_DIR, cfg["file"])
        if not os.path.exists(filepath):
            print(f"[INDEXER] Skipping missing file: {filepath}")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            chunks = json.load(f)

        if not chunks:
            continue

        texts = [chunk["text"] for chunk in chunks]
        print(f"[INDEXER] Embedding '{domain_name}' ({len(texts)} chunks)...")

        embeddings = model.encode(
            texts,
            batch_size=EMBED_BATCH_SIZE,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=True,
        )
        embeddings = np.array(embeddings, dtype=np.float32)

        emb_path = os.path.join(KNOWLEDGE_DIR, f"{domain_name}.npy")
        meta_path = os.path.join(KNOWLEDGE_DIR, f"{domain_name}_meta.pkl")
        faiss_path = os.path.join(KNOWLEDGE_DIR, f"{domain_name}.faiss")

        np.save(emb_path, embeddings)
        with open(meta_path, "wb") as f:
            pickle.dump(chunks, f)

        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(embeddings)
        faiss.write_index(index, faiss_path)

        print(f"[INDEXER] Saved {domain_name} -> {emb_path}, {meta_path}, {faiss_path}")

if __name__ == "__main__":
    run_indexer()
    print("\n[INDEXER] All domains indexed successfully!")
