import os
import asyncio
from server.config import WHISPER_SIZE, MODEL_CACHE_DIR, AUDIO_DIR

_model = None

def _load_model():
    global _model
    if _model is not None:
        return
    import whisper
    print(f"[STT] Loading whisper-{WHISPER_SIZE}...")
    _model = whisper.load_model(
        WHISPER_SIZE,
        device="cpu",
        download_root=os.path.join(MODEL_CACHE_DIR, "whisper"),
    )
    print("[STT] Whisper ready")

def _transcribe_sync(audio_path: str) -> str:
    _load_model()
    result = _model.transcribe(
        audio_path,
        fp16=False,
        language="en",
        task="transcribe",
        beam_size=1,
        best_of=1,
        condition_on_previous_text=False,
    )
    return result["text"].strip()

async def transcribe(audio_path: str) -> str:
    return await asyncio.to_thread(_transcribe_sync, audio_path)
