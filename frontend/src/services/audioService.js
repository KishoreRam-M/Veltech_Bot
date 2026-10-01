/**
 * Audio service — wraps the browser AudioContext, TTS playback queue,
 * and edge-TTS API call.
 *
 * All functions are exported individually so callers import only what they use.
 */

/** Lazily initialise (or resume) the shared AudioContext. */
export async function ensureAudioContext() {
  if (!window.audioCtx) {
    window.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  }
  if (window.audioCtx.state === 'suspended') {
    await window.audioCtx.resume();
  }
}

/**
 * Return the best audio MIME type the current browser supports for MediaRecorder.
 * @returns {string} MIME type string, or empty string (browser default)
 */
export function getBestMimeType() {
  const candidates = [
    'audio/webm;codecs=opus',
    'audio/webm',
    'audio/ogg;codecs=opus',
    'audio/ogg',
  ];
  for (const mime of candidates) {
    if (MediaRecorder.isTypeSupported(mime)) return mime;
  }
  return '';
}

/**
 * Fetch TTS audio URL from the backend and play it.
 *
 * @param {string}   text            - Text to synthesise
 * @param {string}   lang            - Language code ('en'|'ta'|'tanglish')
 * @param {function} onComplete      - Called when playback ends or on error
 * @param {object}   currentAudioRef - Ref holding the active HTMLAudioElement
 * @returns {Promise<void>}
 */
export async function playTtsAudio(text, lang, onComplete, currentAudioRef) {
  const clean = text
    .replace(/[*_#"`~]/g, '')
    .replace(/[🎓🌟🚀💪✨🎯🏆💰🔥👋🙏📚📝💼🏠🏛️⭐🎉⚡🧠🔇🔊₹━•\-]/g, '')
    .trim();

  if (!clean) {
    onComplete();
    return;
  }

  try {
    await ensureAudioContext();

    const response = await fetch('/api/tts/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: clean, lang }),
    });

    if (!response.ok) throw new Error(`TTS HTTP ${response.status}`);
    const data = await response.json();

    if (!data.audio_url) {
      onComplete();
      return;
    }

    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
    }

    const audio = new Audio(data.audio_url);
    currentAudioRef.current = audio;

    audio.onended = () => {
      currentAudioRef.current = null;
      onComplete();
    };
    audio.onerror = () => {
      currentAudioRef.current = null;
      onComplete();
    };

    try {
      await audio.play();
    } catch {
      currentAudioRef.current = null;
      onComplete();
    }
  } catch {
    onComplete();
  }
}

/**
 * Split response text into sentences and enqueue them for TTS playback.
 *
 * @param {string}   text          - Full bot response text
 * @param {string}   lang          - Language code
 * @param {object}   queueRef      - Ref to the TTS sentence queue array
 * @param {object}   speakingRef   - Ref to the boolean "currently playing" flag
 * @param {function} processQueue  - Function to start queue processing
 */
export function enqueueForSpeech(text, lang, queueRef, speakingRef, processQueue) {
  if (!text) return;
  const sentences = text
    .split(/(?<=[.?!])\s+|\n+/)
    .filter((s) => s.trim().length > 0);

  sentences.forEach((sentence) => {
    // For Tanglish, send Tamil-script segments to the Tamil voice
    const resolvedLang =
      lang === 'tanglish' && /[\u0B80-\u0BFF]/.test(sentence) ? 'ta' : lang;
    queueRef.current.push({ text: sentence, language: resolvedLang });
  });

  if (!speakingRef.current) processQueue();
}
