import intel_setup

import os
import json
import numpy as np
import lancedb
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

    db_path = os.path.join(KNOWLEDGE_DIR, "lancedb_store")
    os.makedirs(db_path, exist_ok=True)
    db = lancedb.connect(db_path)

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

        data = []
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            # LanceDB expects the embedding in a column named 'vector'
            row = chunk.copy()
            row["vector"] = emb.tolist()
            row["chunk_id"] = i
            data.append(row)

        db.create_table(domain_name, data=data, mode="overwrite")
        print(f"[INDEXER] Saved {domain_name} -> LanceDB table '{domain_name}'")

if __name__ == "__main__":
    run_indexer()
    print("\n[INDEXER] All domains indexed successfully!")
