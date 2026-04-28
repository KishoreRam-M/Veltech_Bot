import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';

const WELCOME_DATA = {
  en: {
    title: "Your Dream Career Starts Here! 🚀",
    text: "I'm VelBot — your personal AI Admission Counselor. Let me show you why Vel Tech Multi Tech is the BEST choice for your future!",
  },
  ta: {
    title: "உங்கள் கனவு வாழ்க்கை இங்கே தொடங்குகிறது! 🚀",
    text: "நான் VelBot — உங்கள் AI Admission Counselor. Vel Tech Multi Tech உங்கள் எதிர்காலத்திற்கு ஏன் சிறந்த தேர்வு என்று காட்டுகிறேன்!",
  },
  tanglish: {
    title: "Unga Dream Future Starts Here da! 🚀🔥",
    text: "Naan VelBot — unga personal AI Admission Counselor. Vel Tech Multi Tech yenna oru vera level college nu naan solren, nee paaru!",
  },
};

export default function App() {
  const [language, setLanguage] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [status, setStatus] = useState({ state: 'connected', text: 'Online' });
  const [sessionId, setSessionId] = useState(null);
  
  const wsRef = useRef(null);
  const chatEndRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const ttsQueueRef = useRef([]);
  const currentAudioRef = useRef(null);
  const isSpeakingRef = useRef(false);

  // Initialize Audio Context on user interaction
  const initAudio = () => {
    if (!window.audioCtx) {
      window.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (window.audioCtx.state === 'suspended') {
      window.audioCtx.resume();
    }
  };

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const connectWS = () => {
    const protocol = location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${location.host}/ws/chat`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => setStatus({ state: 'connected', text: 'Online' });
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'session') {
        setSessionId(data.session_id);
      } else if (data.type === 'response' || data.type === 'done') {
        setIsTyping(false);
        setMessages(prev => [...prev, { role: 'bot', text: data.text || data.response, meta: data }]);
        autoSpeak(data.text || data.response, data.language);
      } else if (data.type === 'error') {
        setIsTyping(false);
        setMessages(prev => [...prev, { role: 'bot', text: data.text || 'Error occurred', meta: { intent: 'error' } }]);
      }
    };

    ws.onclose = () => {
      setStatus({ state: 'error', text: 'Disconnected' });
      setTimeout(connectWS, 3000);
    };

    wsRef.current = ws;
  };

  useEffect(() => {
    if (language) {
      connectWS();
    }
    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, [language]);

  const processTtsQueue = () => {
    if (ttsQueueRef.current.length > 0) {
      const next = ttsQueueRef.current.shift();
      isSpeakingRef.current = true;
      playTTS(next.text, next.language);
    } else {
      isSpeakingRef.current = false;
    }
  };

  const playTTS = async (text, lang) => {
    const clean = text.replace(/[*_#"`~]/g, "").replace(/[🎓🌟🚀💪✨🎯🏆💰🔥👋🙏📚📝💼🏠🏛️⭐🎉⚡🧠🔇🔊₹━•\-]/g, "").trim();
    if (!clean) return processTtsQueue();

    try {
      const res = await fetch('/api/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: clean, lang: lang || language || 'en' }),
      });
      if (!res.ok) throw new Error('TTS Failed');
      const data = await res.json();
      
      if (!data.audio_url) {
        return processTtsQueue(); // graceful fallback when TTS is unavailable
      }
      
      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
      }
      
      const audio = new Audio(data.audio_url);
      currentAudioRef.current = audio;
      audio.onended = () => { currentAudioRef.current = null; processTtsQueue(); };
      audio.onerror = () => { currentAudioRef.current = null; processTtsQueue(); };
      await audio.play();
    } catch (e) {
      console.error(e);
      processTtsQueue();
    }
  };

  const autoSpeak = (text, lang) => {
    if (isMuted || !text) return;
    const sentences = text.split(/(?<=[.?!])\s+|\n+/).filter(s => s.trim().length > 0);
    sentences.forEach(sentence => {
      let sentenceLang = lang;
      if (lang === "tanglish") {
        sentenceLang = /[\u0B80-\u0BFF]/.test(sentence) ? "ta" : "en";
      }
      ttsQueueRef.current.push({ text: sentence, language: sentenceLang });
    });
    if (!isSpeakingRef.current) processTtsQueue();
  };

  const replaySpeak = (text, lang) => {
    if (!text) return;
    initAudio();
    ttsQueueRef.current = [];
    if (currentAudioRef.current) {
        currentAudioRef.current.pause();
        currentAudioRef.current = null;
    }
    isSpeakingRef.current = false;
    autoSpeak(text, lang);
  }

  const handleSend = async (textOverride) => {
    const text = typeof textOverride === 'string' ? textOverride : input;
    if (!text.trim() || !language) return;
    
    initAudio();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', text }]);
    setIsTyping(true);

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ query: text, language }));
    } else {
      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: text, language, session_id: sessionId })
        });
        const data = await res.json();
        setIsTyping(false);
        if (data.session_id) setSessionId(data.session_id);
        setMessages(prev => [...prev, { role: 'bot', text: data.response, meta: data }]);
        autoSpeak(data.response, data.language);
      } catch (e) {
        setIsTyping(false);
        setMessages(prev => [...prev, { role: 'bot', text: 'Connection failed', meta: { intent: 'error', cache: 'none' } }]);
      }
    }
  };

  const toggleRecording = async () => {
    if (!language) return;
    initAudio();

    if (isRecording) {
      mediaRecorderRef.current?.stop();
      setIsRecording(false);
      setStatus({ state: 'connected', text: 'Processing Audio...' });
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = e => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach(t => t.stop());
        if (audioChunksRef.current.length === 0) return;
        
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const formData = new FormData();
        formData.append("file", audioBlob, "recording.webm");

        try {
          const res = await fetch("/api/stt", { method: "POST", body: formData });
          const data = await res.json();
          if (data.transcript?.trim()) {
            handleSend(data.transcript.trim());
          }
        } catch (e) {
          console.error(e);
        } finally {
          setStatus({ state: 'connected', text: 'Online' });
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
      setStatus({ state: 'connected', text: 'Recording...' });
    } catch (e) {
      console.error("Mic error", e);
    }
  };

  return (
    <>
      {!language && (
        <div className="lang-modal-overlay" id="lang-modal-overlay">
          <div className="lang-modal glass-panel" id="lang-modal">
            <div className="lang-modal-icon">🌏</div>
            <h2 className="lang-modal-title">Hi 👋 Unga preferred language enna?</h2>
            <p className="lang-modal-subtitle">Choose your language to begin your journey!</p>
            <div className="lang-modal-buttons">
              <button className="lang-choice-btn" onClick={() => { initAudio(); setLanguage('ta'); }}>
                <span className="lang-choice-emoji">🇮🇳</span>
                <span className="lang-choice-label">தமிழ்</span>
                <span className="lang-choice-sub">Tamil</span>
              </button>
              <button className="lang-choice-btn" onClick={() => { initAudio(); setLanguage('en'); }}>
                <span className="lang-choice-emoji">🌍</span>
                <span className="lang-choice-label">English</span>
                <span className="lang-choice-sub">English</span>
              </button>
              <button className="lang-choice-btn" onClick={() => { initAudio(); setLanguage('tanglish'); }}>
                <span className="lang-choice-emoji">🔥</span>
                <span className="lang-choice-label">Tanglish</span>
                <span className="lang-choice-sub">Mix it up!</span>
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="toast-container" id="toast-container"></div>

      <div className="app-container" id="app">
        <div className="bg-orbs">
          <div className="orb orb-1"></div>
          <div className="orb orb-2"></div>
          <div className="orb orb-3"></div>
        </div>

        <header className="header glass-panel" id="header">
          <div className="header-left">
            <div className="header-icon-wrap">
              <span className="header-icon">🎓</span>
            </div>
            <div className="header-text">
              <h1>VelBot</h1>
              <p className="subtitle">AI Admissions Counselor</p>
            </div>
          </div>
          <div className="header-right">
            <div className="status-indicator" id="status-indicator">
              <span className={`status-dot ${status.state}`}></span>
              <span className="status-text">{status.text}</span>
            </div>
            <button className={`mute-toggle ${isMuted ? 'muted' : ''}`} onClick={() => {
              setIsMuted(!isMuted);
              if (!isMuted && currentAudioRef.current) currentAudioRef.current.pause();
            }} title="Toggle audio">
              {!isMuted ? (
                <svg className="mute-icon-on" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                  <path d="M19.07 4.93a10 10 0 0 1 0 14.14"></path>
                  <path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path>
                </svg>
              ) : (
                <svg className="mute-icon-off" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
                  <line x1="23" y1="9" x2="17" y2="15"></line>
                  <line x1="17" y1="9" x2="23" y2="15"></line>
                </svg>
              )}
            </button>
            <div className="lang-badge" id="lang-badge" title="Selected language" onClick={() => setLanguage(null)}>
              {language === 'ta' ? 'TA' : language === 'tanglish' ? 'TG' : 'EN'}
            </div>
          </div>
        </header>

        <main className="chat-area" id="chat-area">
          <div className="chat-messages" id="chat-messages">
            {messages.length === 0 && (
              <div className="welcome-card glass-panel" id="welcome-card">
                <div className="welcome-icon">🚀</div>
                <h2 id="welcome-title">{WELCOME_DATA[language]?.title || WELCOME_DATA.en.title}</h2>
                <p id="welcome-text">{WELCOME_DATA[language]?.text || WELCOME_DATA.en.text}</p>
                <div className="quick-actions" id="quick-actions">
                  <button className="quick-btn" onClick={() => handleSend("What courses are offered?")}>📚 Courses</button>
                  <button className="quick-btn" onClick={() => handleSend("How to apply for admission?")}>📝 Apply Now</button>
                  <button className="quick-btn" onClick={() => handleSend("Tell me about placements and salary packages")}>💰 Placements</button>
                  <button className="quick-btn" onClick={() => handleSend("What makes Vel Tech Multi Tech special?")}>⭐ Why Us?</button>
                  <button className="quick-btn" onClick={() => handleSend("What are the fees and scholarships?")}>🎓 Fees & Aid</button>
                  <button className="quick-btn" onClick={() => handleSend("Tell me about campus life, events, and clubs")}>🎉 Campus Life</button>
                </div>
              </div>
            )}

            {messages.map((msg, i) => (
              <div key={i} className={`message ${msg.role}`}>
                <div className="msg-avatar">{msg.role === 'user' ? '👤' : '🤖'}</div>
                <div className="msg-content">
                  {msg.role === 'bot' ? (
                    <div className="markdown-body">
                      <ReactMarkdown>{msg.text}</ReactMarkdown>
                    </div>
                  ) : (
                    <p>{msg.text}</p>
                  )}
                  {msg.role === 'bot' && msg.meta && (
                    <div className="msg-footer">
                      <div className="msg-meta">
                        <span className={`cache-badge ${msg.meta.cache === 'L1' ? 'l1' : msg.meta.cache === 'L2' ? 'l2' : msg.meta.cache === 'crew' ? 'agent' : 'none'}`}>
                          {msg.meta.cache === 'L1' ? '⚡ Cached' : msg.meta.cache === 'L2' ? '🧠 Semantic' : msg.meta.cache === 'crew' ? '🤖 Agent' : 'Generated'}
                        </span>
                        {msg.meta.strategy && <span className="strategy-badge">{msg.meta.strategy.replace(/_/g, ' ')}</span>}
                        {msg.meta.ms && <span>{msg.meta.ms}ms</span>}
                      </div>
                      <button className="msg-speaker-btn" title="Replay audio" onClick={() => replaySpeak(msg.text, msg.meta.language || language)}>🔊</button>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {isTyping && (
              <div className="typing-indicator" id="typing-indicator">
                <div className="msg-avatar" style={{ background: 'linear-gradient(135deg,#6366f1,#8b5cf6)' }}>🤖</div>
                <div className="typing-dots">
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                </div>
              </div>
            )}
            
            <div ref={chatEndRef} />
          </div>
        </main>

        <footer className="input-area glass-panel" id="input-area">
          <div className="input-wrapper">
            <button className={`voice-btn ${isRecording ? 'recording' : ''}`} id="voice-btn" title="Voice input (beta)" onClick={toggleRecording}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                <line x1="12" y1="19" x2="12" y2="23"/>
                <line x1="8" y1="23" x2="16" y2="23"/>
              </svg>
              <span className="voice-beta-tag">β</span>
            </button>
            <input 
              type="text" 
              id="chat-input" 
              placeholder="Ask about courses, admissions, placements..." 
              autoComplete="off" 
              maxLength="500"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleSend();
              }}
            />
            <button className="send-btn" id="send-btn" title="Send message" onClick={() => handleSend()}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13"/>
                <polygon points="22 2 15 22 11 13 2 9 22 2"/>
              </svg>
            </button>
          </div>
          <p className="input-hint">Press Enter to send • 🎤 Voice (beta) • Supports Tamil, English & Tanglish</p>
        </footer>
      </div>
    </>
  );
}
