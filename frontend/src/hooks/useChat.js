import { useState, useEffect, useRef, useCallback } from 'react';
import { connectWebSocket, sendMessage, transcribeAudio } from '../services/chatService';

export function useChat(language) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [status, setStatus] = useState({ state: 'connected', text: 'Online' });
  const [sessionId, setSessionId] = useState(null);
  const wsRef = useRef(null);
  const chatEndRef = useRef(null);
  
  const addBotMessage = useCallback((text, meta) => {
    setIsTyping(false);
    setMessages((prev) => [...prev, { role: 'bot', text, meta }]);
  }, []);

  const connectWS = useCallback(() => {
    if (!language) return;
    const ws = connectWebSocket(
      (sid) => setSessionId(sid),
      ({ text, meta }) => addBotMessage(text, meta),
      () => {
        setStatus({ state: 'error', text: 'Disconnected' });
        setTimeout(connectWS, 3000);
      }
    );
    ws.onopen = () => setStatus({ state: 'connected', text: 'Online' });
    wsRef.current = ws;
  }, [language, addBotMessage]);

  useEffect(() => {
    connectWS();
    return () => wsRef.current?.close();
  }, [connectWS]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const handleSend = useCallback(async (textOverride) => {
    const text = typeof textOverride === 'string' ? textOverride : input;
    if (!text.trim() || !language) return;
    
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', text }]);
    setIsTyping(true);

    try {
      const data = await sendMessage(wsRef.current, text, language, sessionId);
      if (data) {
        if (data.session_id) setSessionId(data.session_id);
        addBotMessage(data.response, data);
      }
    } catch {
      setIsTyping(false);
      setMessages((prev) => [
        ...prev,
        { role: 'bot', text: 'Connection failed.', meta: { intent: 'error' } },
      ]);
    }
  }, [input, language, sessionId, addBotMessage]);

  return {
    messages, input, setInput, isTyping, status, setStatus, handleSend, chatEndRef, addBotMessage
  };
}
