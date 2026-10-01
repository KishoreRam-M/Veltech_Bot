import { Globe, MapPin, Sparkles } from 'lucide-react';

/**
 * Language selector modal shown before the chat begins.
 *
 * @param {function} onSelect - Called with the chosen language code ('en'|'ta'|'tanglish')
 */
export default function LanguageModal({ onSelect }) {
  return (
    <div className="lang-modal-overlay" id="lang-modal-overlay">
      <div className="lang-modal glass-panel" id="lang-modal">
        <div className="lang-modal-icon"><Globe size={36} /></div>
        <h2 className="lang-modal-title">Hi 👋 <span>Unga preferred language enna?</span></h2>
        <p className="lang-modal-subtitle">Choose your language to begin your journey!</p>
        <div className="lang-modal-buttons">
          <button className="lang-choice-btn" id="lang-btn-ta" onClick={() => onSelect('ta')}>
            <MapPin className="lang-choice-icon" size={28} />
            <span className="lang-choice-label">தமிழ்</span>
            <span className="lang-choice-sub">Tamil</span>
          </button>
          <button className="lang-choice-btn" id="lang-btn-en" onClick={() => onSelect('en')}>
            <Globe className="lang-choice-icon" size={28} />
            <span className="lang-choice-label">English</span>
            <span className="lang-choice-sub">English</span>
          </button>
          <button className="lang-choice-btn" id="lang-btn-tanglish" onClick={() => onSelect('tanglish')}>
            <Sparkles className="lang-choice-icon" size={28} />
            <span className="lang-choice-label">Tanglish</span>
            <span className="lang-choice-sub">Mix it up!</span>
          </button>
        </div>
      </div>
    </div>
  );
}
