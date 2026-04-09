import numpy as np
from sentence_transformers import SentenceTransformer
from server.config import EMBEDDING_MODEL, MODEL_CACHE_DIR, EMBED_BATCH_SIZE
import asyncio

_model = None

def _get_model():
    global _model
    if _model is None:
        print(f"[KB] Loading embedding model {EMBEDDING_MODEL}...")
        _model = SentenceTransformer(
            EMBEDDING_MODEL,
            device="cpu",
            cache_folder=MODEL_CACHE_DIR,
        )
        print("[KB] Embedding model ready")
    return _model

async def embed_texts(texts: list[str]) -> np.ndarray:
    model = _get_model()
    def _encode():
        return model.encode(
            texts,
            batch_size=EMBED_BATCH_SIZE,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
    vecs = await asyncio.to_thread(_encode)
    return vecs.astype(np.float32)

async def embed_single(text: str) -> np.ndarray:
    result = await embed_texts([text])
    return result[0]
