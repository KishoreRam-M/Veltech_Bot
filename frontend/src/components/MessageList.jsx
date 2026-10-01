import ReactMarkdown from 'react-markdown';
import { BookOpen, GraduationCap, Briefcase, Star, IndianRupee, Users, User, Bot, Volume2 } from 'lucide-react';

/** Quick-action prompts shown on the welcome screen. */
const QUICK_PROMPTS = [
  { label: 'Courses', icon: BookOpen, text: 'What courses are offered?' },
  { label: 'Apply Now', icon: GraduationCap, text: 'How to apply for admission?' },
  { label: 'Placements', icon: Briefcase, text: 'Tell me about placements and salary packages' },
  { label: 'Why Us?', icon: Star, text: 'What makes Vel Tech Multi Tech special?' },
  { label: 'Fees & Aid', icon: IndianRupee, text: 'What are the fees and scholarships?' },
  { label: 'Campus Life', icon: Users, text: 'Tell me about campus life, events, and clubs' },
];

const CACHE_LABELS = {
  L1:   { cls: 'l1',    text: '⚡ Cached' },
  L2:   { cls: 'l2',    text: '🧠 Semantic' },
  crew: { cls: 'agent', text: '🤖 Agent' },
};

/**
 * Scrollable chat message list with welcome card and typing indicator.
 *
 * @param {Array}    messages   - Array of { role, text, meta } objects
 * @param {boolean}  isTyping   - Whether the bot is currently generating
 * @param {string}   language   - Active language code
 * @param {function} onSend     - Called with a text string when quick-action clicked
 * @param {function} onReplay   - Called with (text, lang) to replay TTS for a message
 * @param {object}   welcomeData - { title, text } for the welcome card
 * @param {object}   chatEndRef  - Ref to the scroll anchor element
 */
export default function MessageList({
  messages, isTyping, language, onSend, onReplay, welcomeData, chatEndRef,
}) {
  return (
    <main className="chat-area" id="chat-area">
      <div className="chat-messages" id="chat-messages">
        {messages.length === 0 && (
          <div className="welcome-card glass-panel" id="welcome-card">
            <div className="welcome-icon"><GraduationCap size={32} /></div>
            <h2 id="welcome-title">{welcomeData.title}</h2>
            <p id="welcome-text">{welcomeData.text}</p>
            <div className="quick-actions" id="quick-actions">
              {QUICK_PROMPTS.map(({ label, icon: Icon, text }) => (
                <button key={label} className="quick-btn" onClick={() => onSend(text)}>
                  <Icon className="quick-btn-icon" size={16} />
                  {label}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, index) => {
          const cacheInfo = CACHE_LABELS[msg.meta?.cache] ?? { cls: 'none', text: 'Generated' };
          return (
            <div key={index} className={`message ${msg.role}`}>
              <div className="msg-avatar">{msg.role === 'user' ? <User size={20} /> : <Bot size={20} />}</div>
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
                      <span className={`cache-badge ${cacheInfo.cls}`}>{cacheInfo.text}</span>
                      {msg.meta.strategy && (
                        <span className="strategy-badge">
                          {msg.meta.strategy.replace(/_/g, ' ')}
                        </span>
                      )}
                      {msg.meta.ms && <span>{msg.meta.ms}ms</span>}
                    </div>
                    <button
                      className="msg-speaker-btn"
                      title="Replay audio"
                      onClick={() => onReplay(msg.text, msg.meta.language || language)}
                    >
                      <Volume2 size={16} />
                    </button>
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {isTyping && (
          <div className="typing-indicator" id="typing-indicator">
            <div className="msg-avatar" style={{ background: 'linear-gradient(135deg,#6366f1,#8b5cf6)' }}>
              <Bot size={20} />
            </div>
            <div className="typing-dots">
              <div className="typing-dot" />
              <div className="typing-dot" />
              <div className="typing-dot" />
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>
    </main>
  );
}
