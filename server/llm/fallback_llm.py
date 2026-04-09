import asyncio
import torch
from server.config import FALLBACK_LLM_MODEL, MODEL_CACHE_DIR

_tokenizer = None
_model = None
_loaded = False

def _load_model():
    global _tokenizer, _model, _loaded
    if _loaded:
        return
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    print(f"[FALLBACK] Loading {FALLBACK_LLM_MODEL} (offline mode)...")
    _tokenizer = AutoTokenizer.from_pretrained(
        FALLBACK_LLM_MODEL,
        cache_dir=MODEL_CACHE_DIR,
    )
    _model = AutoModelForSeq2SeqLM.from_pretrained(
        FALLBACK_LLM_MODEL,
        cache_dir=MODEL_CACHE_DIR,
        torch_dtype=torch.float32,
    )
    _model.eval()
    _loaded = True
    print("[FALLBACK] FLAN-T5-large ready")

def _generate_sync(prompt: str) -> str:
    _load_model()
    inputs = _tokenizer(
        prompt,
        return_tensors="pt",
        max_length=512,
        truncation=True,
    )
    with torch.no_grad():
        outputs = _model.generate(
            **inputs,
            max_new_tokens=300,
            temperature=0.2,
            do_sample=True,
            top_p=0.8,
        )
    return _tokenizer.decode(outputs[0], skip_special_tokens=True)

async def fallback_generate(query: str, chunks: list[dict]) -> str:
    context = "\n\n".join([
        f"[{chunk.get('id', 'unknown')}] {chunk['text']}"
        for chunk in chunks
    ])
    prompt = (
        f"You are a college admissions assistant. "
        f"Answer ONLY using the provided context. "
        f"If the answer is not in the context, say 'This information is not available in the uploaded documents.'\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {query}\n\n"
        f"Answer:"
    )
    return await asyncio.to_thread(_generate_sync, prompt)
