"""
Session Manager for ORCA Backend (SIH26176)
Maintains multi-turn conversational context, user spatial tracking,
and query-response history for maritime decision support.
"""

import time
import uuid
from typing import Dict, List, Optional, Any
from backend.models.response import SessionHistoryItem, HistoryResponse


class SessionData:
    """Container for a single user's multi-turn session."""

    def __init__(self, session_id: str, preferred_language: str = "en"):
        self.session_id = session_id
        self.preferred_language = preferred_language
        self.created_at = time.time()
        self.updated_at = time.time()
        self.last_latitude: Optional[float] = None
        self.last_longitude: Optional[float] = None
        self.history: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}

    def add_turn(
        self,
        query_id: str,
        user_query: str,
        recommendation: str,
        risk_level: str,
        risk_score: float,
        latitude: float,
        longitude: float,
        agent_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Append a conversational turn to this session."""
        self.last_latitude = latitude
        self.last_longitude = longitude
        self.updated_at = time.time()

        turn_item = {
            "query_id": query_id,
            "user_query": user_query,
            "recommendation": recommendation,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "latitude": latitude,
            "longitude": longitude,
            "agent_data": agent_data or {}
        }
        self.history.append(turn_item)

    def to_history_response(self) -> HistoryResponse:
        """Convert session history to Pydantic HistoryResponse model."""
        items = [
            SessionHistoryItem(
                query_id=h["query_id"],
                user_query=h["user_query"],
                recommendation=h["recommendation"],
                risk_level=h["risk_level"],
                risk_score=h["risk_score"],
                timestamp=h["timestamp"],
                latitude=h["latitude"],
                longitude=h["longitude"]
            )
            for h in self.history
        ]
        return HistoryResponse(
            session_id=self.session_id,
            total_turns=len(items),
            history=items
        )


class SessionManager:
    """Thread-safe In-Memory session manager with LRU eviction."""

    def __init__(self, max_sessions: int = 1000, session_ttl_seconds: int = 86400):
        self._sessions: Dict[str, SessionData] = {}
        self.max_sessions = max_sessions
        self.session_ttl = session_ttl_seconds

    def get_or_create_session(self, session_id: Optional[str] = None, language_code: str = "en") -> SessionData:
        """Retrieve existing session or create a new one."""
        sid = session_id.strip() if session_id and session_id.strip() else f"orca-{uuid.uuid4().hex[:8]}"

        self._cleanup_stale()

        if sid not in self._sessions:
            if len(self._sessions) >= self.max_sessions:
                # Evict oldest
                oldest_sid = min(self._sessions.keys(), key=lambda k: self._sessions[k].updated_at)
                del self._sessions[oldest_sid]
            self._sessions[sid] = SessionData(session_id=sid, preferred_language=language_code)

        session = self._sessions[sid]
        if language_code and language_code != "en":
            session.preferred_language = language_code
        return session

    def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get existing session by ID."""
        return self._sessions.get(session_id)

    def list_active_sessions(self) -> List[Dict[str, Any]]:
        """List active session IDs and metadata."""
        return [
            {
                "session_id": s.session_id,
                "turns": len(s.history),
                "created_at": s.created_at,
                "updated_at": s.updated_at,
                "preferred_language": s.preferred_language,
                "last_location": {
                    "latitude": s.last_latitude,
                    "longitude": s.last_longitude
                } if s.last_latitude is not None else None
            }
            for s in self._sessions.values()
        ]

    def delete_session(self, session_id: str) -> bool:
        """Delete session by ID."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def clear_all(self) -> None:
        """Clear all sessions."""
        self._sessions.clear()

    def _cleanup_stale(self) -> None:
        """Remove sessions older than TTL."""
        now = time.time()
        stale_ids = [
            sid for sid, s in self._sessions.items()
            if (now - s.updated_at) > self.session_ttl
        ]
        for sid in stale_ids:
            del self._sessions[sid]


# Global session manager instance
session_manager = SessionManager()
