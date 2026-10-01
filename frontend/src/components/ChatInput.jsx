import { Mic, Send, MessageSquare } from 'lucide-react';

/**
 * Chat input bar with voice recording toggle and send button.
 *
 * @param {string}   value        - Controlled input value
 * @param {function} onChange     - Called with new input string
 * @param {function} onSend       - Called to submit current input
 * @param {function} onVoice      - Toggles voice recording
 * @param {boolean}  isRecording  - Whether microphone is active
 * @param {boolean}  disabled     - Disables input when no language selected
 */
export default function ChatInput({ value, onChange, onSend, onVoice, isRecording, disabled }) {
  const handleKeyDown = (event) => {
    if (event.key === 'Enter') onSend();
  };

  return (
    <footer className="input-area glass-panel" id="input-area">
      <div className="input-wrapper">
        <button
          className={`voice-btn ${isRecording ? 'recording' : ''}`}
          id="voice-btn"
          title="Voice input (beta)"
          onClick={onVoice}
          disabled={disabled}
        >
          <Mic size={20} />
          <span className="voice-beta-tag">β</span>
        </button>

        <input
          type="text"
          id="chat-input"
          placeholder="Ask about courses, admissions, placements..."
          autoComplete="off"
          maxLength={500}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
        />

        <button
          className="send-btn"
          id="send-btn"
          title="Send message"
          onClick={onSend}
          disabled={disabled}
        >
          <Send size={20} />
        </button>
      </div>
      <p className="input-hint">
        Press Enter to send • 🎤 Voice (beta) • Supports Tamil, English & Tanglish
      </p>
    </footer>
  );
}
