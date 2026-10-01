import { GraduationCap, Volume2, VolumeX, Sun, Moon } from 'lucide-react';

/**
 * Chat header bar with status dot, mute toggle, theme toggle, and language badge.
 *
 * @param {object}   status          - { state: 'connected'|'error', text: string }
 * @param {boolean}  isMuted         - Whether TTS audio is muted
 * @param {function} onMute          - Toggle mute state
 * @param {string}   language        - Currently selected language code
 * @param {function} onLangReset     - Called when user clicks the language badge to reset
 * @param {boolean}  isDark          - Whether dark mode is active
 * @param {function} onToggleTheme   - Toggle dark/light mode
 */
export default function ChatHeader({ status, isMuted, onMute, language, onLangReset, isDark, onToggleTheme }) {
  const langLabel = language === 'ta' ? 'TA' : language === 'tanglish' ? 'TG' : 'EN';

  return (
    <header className="header glass-panel" id="header">
      <div className="header-left">
        <div className="header-icon-wrap">
          <GraduationCap size={24} />
        </div>
        <div className="header-text">
          <h1>VelBot</h1>
          <p className="subtitle">AI Admissions Counselor</p>
        </div>
      </div>
      <div className="header-right">
        <div className="status-indicator" id="status-indicator">
          <span className={`status-dot ${status.state}`} />
          <span className="status-text">{status.text}</span>
        </div>

        <button
          className="theme-toggle"
          id="theme-toggle-btn"
          onClick={onToggleTheme}
          title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {isDark ? <Sun size={17} /> : <Moon size={17} />}
        </button>

        <button
          className={`mute-toggle ${isMuted ? 'muted' : ''}`}
          id="mute-btn"
          onClick={onMute}
          title="Toggle audio"
        >
          {!isMuted ? (
            <Volume2 size={18} />
          ) : (
            <VolumeX size={18} />
          )}
        </button>

        <div
          className="lang-badge"
          id="lang-badge"
          title="Click to change language"
          onClick={onLangReset}
        >
          {langLabel}
        </div>
      </div>
    </header>
  );
}
