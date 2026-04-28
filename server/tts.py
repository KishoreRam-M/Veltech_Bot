"""TTS module — edge-tts with robust fallback chain.

Voice priority (per language):
  en / tanglish:
    1. en-IN-NeerjaExpressiveNeural  (expressive, may be region-locked)
    2. en-IN-NeerjaNeural            (standard IN female)
    3. en-US-JennyNeural             (US fallback, always available)
    4. en-GB-SoniaNeural             (UK last-resort)
  ta:
    1. ta-IN-PallaviNeural
    2. ta-IN-ValluvarNeural
    3. en-IN-NeerjaNeural            (language-mismatch last-resort)

403 / ConnectionError → token may have expired.  edge_tts.Communicate
automatically refreshes the TrustedClientToken on each instantiation, so
retrying with a short back-off is the correct fix.

Every voice attempt has a 20-second asyncio timeout to prevent hanging
requests from blocking the event-loop.
"""

import asyncio
import glob
import logging
import os
import re
import time
import uuid

import edge_tts

from server.config import AUDIO_DIR

log = logging.getLogger(__name__)

# ── Voice chains ──────────────────────────────────────────────────────────────
# First available voice that succeeds will be used.

VOICE_CHAINS: dict[str, list[str]] = {
    "en": [
        "en-IN-NeerjaExpressiveNeural",
        "en-IN-NeerjaNeural",
        "en-US-JennyNeural",
        "en-GB-SoniaNeural",
    ],
    "ta": [
        "ta-IN-PallaviNeural",
        "ta-IN-ValluvarNeural",
        "en-IN-NeerjaNeural",   # last-resort: wrong language but still audible
    ],
    "tanglish": [
        "en-IN-NeerjaExpressiveNeural",
        "en-IN-NeerjaNeural",
        "en-US-JennyNeural",
        "en-GB-SoniaNeural",
    ],
}

RATE_NORMAL = "+0%"
RATE_SLOW = "-8%"
PITCH = "+0Hz"
LONG_TEXT_THRESHOLD = 400

MAX_AUDIO_AGE_SECONDS = 300
MAX_AUDIO_FILES = 50
TTS_TIMEOUT_SECONDS = 20       # hard cap per voice attempt
RETRY_BACKOFF_BASE = 0.5       # seconds; doubled on each retry


# ── Audio hygiene ─────────────────────────────────────────────────────────────

def _cleanup_old_audio() -> None:
    try:
        files = glob.glob(os.path.join(AUDIO_DIR, "*.mp3"))
        if len(files) > MAX_AUDIO_FILES:
            files.sort(key=os.path.getmtime)
            for f in files[: len(files) - MAX_AUDIO_FILES]:
                try:
                    os.remove(f)
                except Exception:
                    pass

        now = time.time()
        for f in glob.glob(os.path.join(AUDIO_DIR, "*.mp3")):
            try:
                if now - os.path.getmtime(f) > MAX_AUDIO_AGE_SECONDS:
                    os.remove(f)
            except Exception:
                pass
    except Exception:
        pass


# ── Text sanitiser ────────────────────────────────────────────────────────────

_EMOJI_RE = re.compile(
    r"[🎓🌟🚀💪✨🎯🏆💰🔥👋🙏📚📝💼🏠🏛️⭐🎉⚡🧠🔇🔊₹━•\-]"
)


def _sanitise(text: str, max_chars: int = 2000) -> str:
    clean = _EMOJI_RE.sub("", text).strip()
    return clean[:max_chars]


# ── Core synthesis ────────────────────────────────────────────────────────────

async def _try_voice(voice: str, text: str, rate: str, filepath: str) -> bool:
    """Attempt TTS with a single voice.  Returns True on success."""
    try:
        communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=PITCH)
        await asyncio.wait_for(communicate.save(filepath), timeout=TTS_TIMEOUT_SECONDS)

        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            return True

        # File written but empty — clean up and fall through
        _safe_remove(filepath)
        return False

    except asyncio.TimeoutError:
        log.warning("[TTS] Voice %s timed out after %ss", voice, TTS_TIMEOUT_SECONDS)
    except Exception as e:
        # 403 = token issue  |  ConnectionError = network blip
        log.warning("[TTS] Voice %s failed: %s", voice, e)

    _safe_remove(filepath)
    return False


def _safe_remove(path: str) -> None:
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


# ── Public API ────────────────────────────────────────────────────────────────

async def generate_tts_audio(text: str, language: str) -> str:
    """Generate MP3 audio for *text* and return the filename (or '' on failure).

    Walks the full voice chain for the detected language.  Each voice gets up
    to 2 attempts (with exponential back-off) before the next is tried.
    If all voices fail the function returns '' so callers can degrade gracefully
    instead of propagating a 500.
    """
    _cleanup_old_audio()

    clean_text = _sanitise(text)
    if not clean_text:
        return ""

    rate = RATE_SLOW if len(clean_text) > LONG_TEXT_THRESHOLD else RATE_NORMAL
    voice_chain = VOICE_CHAINS.get(language, VOICE_CHAINS["en"])

    filename = f"tts_{uuid.uuid4().hex[:12]}.mp3"
    filepath = os.path.join(AUDIO_DIR, filename)

    for voice in voice_chain:
        for attempt in range(2):          # 2 attempts per voice (handles stale token)
            if attempt > 0:
                backoff = RETRY_BACKOFF_BASE * (2 ** (attempt - 1))
                log.debug("[TTS] Retry %s for %s (back-off %.1fs)", attempt, voice, backoff)
                await asyncio.sleep(backoff)

            if await _try_voice(voice, clean_text, rate, filepath):
                log.info("[TTS] Success with voice=%s lang=%s len=%d", voice, language, len(clean_text))
                return filename

    log.error(
        "[TTS] All voices exhausted for lang=%s — returning empty (TTS disabled for this response)",
        language,
    )
    return ""
