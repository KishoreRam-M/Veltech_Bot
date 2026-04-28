"""In-memory session state manager for per-user conversation tracking."""

import time
from dataclasses import dataclass, field


@dataclass
class SessionState:
    session_id: str
    language: str | None = None          # "ta", "en", "tanglish", or None (auto)
    user_name: str | None = None
    history: list[dict] = field(default_factory=list)   # [{role, text}]
    interests: list[str] = field(default_factory=list)  # courses, goals mentioned
    strategies_used: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)

    def add_user_message(self, text: str):
        self.history.append({"role": "user", "text": text})
        # Keep only last 10 turns
        if len(self.history) > 20:
            self.history = self.history[-20:]
        self.last_active = time.time()

    def add_bot_message(self, text: str):
        self.history.append({"role": "bot", "text": text})
        if len(self.history) > 20:
            self.history = self.history[-20:]
        self.last_active = time.time()

    def add_interest(self, interest: str):
        if interest and interest not in self.interests:
            self.interests.append(interest)
            # Keep last 10 interests
            if len(self.interests) > 10:
                self.interests = self.interests[-10:]

    def mark_strategy(self, strategy: str):
        if strategy and strategy not in self.strategies_used:
            self.strategies_used.append(strategy)

    def get_conversation_context(self, max_turns: int = 6) -> str:
        """Return recent conversation as text for LLM context."""
        recent = self.history[-(max_turns * 2):]
        lines = []
        for msg in recent:
            role = "Student" if msg["role"] == "user" else "Counselor"
            lines.append(f"{role}: {msg['text']}")
        return "\n".join(lines)


class SessionManager:
    """Thread-safe in-memory session store with TTL cleanup."""

    def __init__(self, ttl_seconds: int = 3600):
        self._sessions: dict[str, SessionState] = {}
        self._ttl = ttl_seconds

    def get_or_create(self, session_id: str) -> SessionState:
        self._cleanup()
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionState(session_id=session_id)
        session = self._sessions[session_id]
        session.last_active = time.time()
        return session

    def get(self, session_id: str) -> SessionState | None:
        return self._sessions.get(session_id)

    def _cleanup(self):
        now = time.time()
        if not hasattr(self, '_last_cleanup'):
            self._last_cleanup = now
        if now - self._last_cleanup < 60:
            return
        self._last_cleanup = now
        expired = [
            sid for sid, s in self._sessions.items()
            if now - s.last_active > self._ttl
        ]
        for sid in expired:
            del self._sessions[sid]


# Global singleton
session_manager = SessionManager(ttl_seconds=7200)  # 2 hours TTL
