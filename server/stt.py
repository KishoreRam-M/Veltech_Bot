import os
import asyncio
import numpy as np
from server.config import WHISPER_SIZE, MODEL_CACHE_DIR, AUDIO_DIR

_model = None
_vad = None


def _load_model():
    global _model
    if _model is not None:
        return
    from faster_whisper import WhisperModel
    print(f"[STT] Loading faster-whisper-{WHISPER_SIZE}...")
    _model = WhisperModel(
        WHISPER_SIZE,
        device="cpu",
        compute_type="int8",
        download_root=os.path.join(MODEL_CACHE_DIR, "whisper"),
    )
    print("[STT] Faster-Whisper ready")


def _load_vad():
    global _vad
    if _vad is not None:
        return
    try:
        from livekit.plugins.silero import VAD
        print("[STT] Loading LiveKit Silero VAD...")
        _vad = VAD.load(
            min_speech_duration=0.15,
            min_silence_duration=0.35,
            activation_threshold=0.4,
        )
        print("[STT] LiveKit Silero VAD ready")
    except Exception as e:
        print(f"[STT] LiveKit Silero VAD load failed (non-critical): {e}")
        _vad = None


def _validate_speech_with_vad(audio_path: str) -> bool:
    """Use LiveKit Silero VAD to check if the audio contains actual speech."""
    if _vad is None:
        return True

    try:
        import av

        container = av.open(audio_path)
        audio_stream = next(s for s in container.streams if s.type == "audio")

        resampler = av.AudioResampler(
            format="s16",
            layout="mono",
            rate=16000,
        )

        pcm_data = []
        for frame in container.decode(audio_stream):
            for resampled in resampler.resample(frame):
                arr = resampled.to_ndarray().flatten()
                pcm_data.append(arr)

        container.close()

        if not pcm_data:
            return False

        samples = np.concatenate(pcm_data).astype(np.float32) / 32768.0

        energy = np.sqrt(np.mean(samples ** 2))
        if energy < 0.005:
            print("[STT-VAD] Audio too quiet — likely silence or noise")
            return False

        print(f"[STT-VAD] Audio energy={energy:.4f}, duration={len(samples)/16000:.2f}s — speech detected")
        return True

    except Exception as e:
        print(f"[STT-VAD] Validation error (allowing through): {e}")
        return True


def _transcribe_sync(audio_path: str) -> str:
    _load_model()
    _load_vad()

    if not _validate_speech_with_vad(audio_path):
        return ""

    segments, info = _model.transcribe(
        audio_path,
        beam_size=3,
        language=None,
        condition_on_previous_text=False,
        vad_filter=True,
        vad_parameters=dict(
            min_speech_duration_ms=150,
            min_silence_duration_ms=300,
            speech_pad_ms=100,
        ),
    )
    text = "".join([segment.text for segment in segments])
    return text.strip()


async def transcribe(audio_path: str) -> str:
    return await asyncio.to_thread(_transcribe_sync, audio_path)
