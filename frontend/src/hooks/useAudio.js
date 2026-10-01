import { useState, useRef, useCallback } from 'react';
import { ensureAudioContext, getBestMimeType, playTtsAudio, enqueueForSpeech } from '../services/audioService';
import { transcribeAudio } from '../services/chatService';

export function useAudio(language, handleSend, setStatus) {
  const [isMuted, setIsMuted] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const ttsQueueRef = useRef([]);
  const currentAudioRef = useRef(null);
  const isSpeakingRef = useRef(false);

  const processQueue = useCallback(() => {
    if (ttsQueueRef.current.length > 0) {
      const { text, language: lang } = ttsQueueRef.current.shift();
      isSpeakingRef.current = true;
      playTtsAudio(text, lang, processQueue, currentAudioRef);
    } else {
      isSpeakingRef.current = false;
    }
  }, []);

  const speak = useCallback((text, lang) => {
    if (isMuted || !text) return;
    enqueueForSpeech(text, lang, ttsQueueRef, isSpeakingRef, processQueue);
  }, [isMuted, processQueue]);

  const replaySpeak = useCallback((text, lang) => {
    if (!text) return;
    ensureAudioContext();
    ttsQueueRef.current = [];
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
    }
    isSpeakingRef.current = false;
    enqueueForSpeech(text, lang, ttsQueueRef, isSpeakingRef, processQueue);
  }, [processQueue]);

  const toggleRecording = useCallback(async () => {
    if (!language) return;
    await ensureAudioContext();

    if (isRecording) {
      mediaRecorderRef.current?.stop();
      setIsRecording(false);
      setStatus({ state: 'connected', text: 'Processing voice...' });
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = getBestMimeType();
      const recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;
      audioChunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data?.size > 0) audioChunksRef.current.push(e.data);
      };
      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        if (audioChunksRef.current.length === 0) {
           setStatus({ state: 'connected', text: 'Online' });
           return;
        }
        const recordedMime = recorder.mimeType || 'audio/webm';
        const blob = new Blob(audioChunksRef.current, { type: recordedMime });
        try {
          const transcript = await transcribeAudio(blob, recordedMime);
          if (transcript) handleSend(transcript);
        } catch {
        } finally {
          setStatus({ state: 'connected', text: 'Online' });
        }
      };

      recorder.start(250);
      setIsRecording(true);
      setStatus({ state: 'connected', text: '🎤 Recording...' });
    } catch {
      setStatus({ state: 'connected', text: 'Online' });
    }
  }, [language, isRecording, handleSend, setStatus]);

  const handleMuteToggle = useCallback(() => {
    setIsMuted((prev) => {
      if (!prev && currentAudioRef.current) currentAudioRef.current.pause();
      return !prev;
    });
  }, []);

  return { isMuted, isRecording, speak, replaySpeak, toggleRecording, handleMuteToggle };
}
