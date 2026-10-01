import { useState, useCallback, useEffect } from 'react';
import LanguageModal from './components/LanguageModal';
import ChatHeader    from './components/ChatHeader';
import MessageList   from './components/MessageList';
import ChatInput     from './components/ChatInput';
import { useChat }   from './hooks/useChat';
import { useAudio }  from './hooks/useAudio';
import { ensureAudioContext } from './services/audioService';

const WELCOME_DATA = {
  en: { title: 'Your Dream Career Starts Here! 🚀', text: "I'm VelBot — your personal AI Admission Counselor. Let me show you why Vel Tech Multi Tech is the BEST choice for your future!" },
  ta: { title: 'உங்கள் கனவு வாழ்க்கை இங்கே தொடங்குகிறது! 🚀', text: 'நான் VelBot — உங்கள் AI Admission Counselor. Vel Tech Multi Tech உங்கள் எதிர்காலத்திற்கு ஏன் சிறந்த தேர்வு என்று காட்டுகிறேன்!' },
  tanglish: { title: 'Unga Dream Future Starts Here da! 🚀🔥', text: 'Naan VelBot — unga personal AI Admission Counselor. Vel Tech Multi Tech yenna oru vera level college nu naan solren, nee paaru!' },
};

export default function App() {
  const [language, setLanguage] = useState(null);
  const [isDark, setIsDark] = useState(() => {
    const saved = localStorage.getItem('velbot-theme');
    return saved ? saved === 'dark' : window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  const { messages, input, setInput, isTyping, status, setStatus, handleSend, chatEndRef, addBotMessage } = useChat(language);
  const { isMuted, isRecording, replaySpeak, toggleRecording, handleMuteToggle, speak } = useAudio(language, handleSend, setStatus);

  // Apply dark mode to <html> element and persist preference
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
    localStorage.setItem('velbot-theme', isDark ? 'dark' : 'light');
  }, [isDark]);

  const toggleTheme = useCallback(() => setIsDark(d => !d), []);

  // Override addBotMessage to include speaking
  const handleBotMessage = useCallback((text, meta) => {
    addBotMessage(text, meta);
    speak(text, meta?.language || language);
  }, [addBotMessage, speak, language]);

  const handleLanguageSelect = useCallback((lang) => {
    ensureAudioContext();
    setLanguage(lang);
  }, []);

  const welcomeData = WELCOME_DATA[language] ?? WELCOME_DATA.en;

  return (
    <>
      {!language && <LanguageModal onSelect={handleLanguageSelect} />}
      <div className="toast-container" id="toast-container" />
      <div className="app-container" id="app">
        <div className="bg-orbs">
          <div className="orb orb-1" /><div className="orb orb-2" /><div className="orb orb-3" />
        </div>
        <ChatHeader
          status={status}
          isMuted={isMuted}
          onMute={handleMuteToggle}
          language={language}
          onLangReset={() => setLanguage(null)}
          isDark={isDark}
          onToggleTheme={toggleTheme}
        />
        <MessageList messages={messages} isTyping={isTyping} language={language} onSend={handleSend} onReplay={replaySpeak} welcomeData={welcomeData} chatEndRef={chatEndRef} />
        <ChatInput value={input} onChange={setInput} onSend={handleSend} onVoice={toggleRecording} isRecording={isRecording} disabled={!language} />
      </div>
    </>
  );
}
