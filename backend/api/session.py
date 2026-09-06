"""
Session API Endpoints & State Helpers for ORCA (SIH26176)
Exposes session lifecycle, multi-turn history retrieval, and session cleanup endpoints.
"""

from fastapi import APIRouter, HTTPException, Path
from typing import Dict, Any, List
from backend.services.session_manager import session_manager
from backend.models.response import HistoryResponse
from backend.models.request import SessionCreateRequest

session_router = APIRouter(prefix="/sessions", tags=["Session State"])


@session_router.get("", response_model=List[Dict[str, Any]], summary="List all active user sessions")
async def list_sessions():
    """Retrieve metadata of all active multi-turn sessions."""
    return session_manager.list_active_sessions()


@session_router.post("/create", summary="Initialize a new session")
async def create_session(payload: SessionCreateRequest):
    """Explicitly create a new session with language and initial coordinate context."""
    session = session_manager.get_or_create_session(
        session_id=None,
        language_code=payload.preferred_language
    )
    if payload.initial_location:
        session.last_latitude = payload.initial_location.get("latitude")
        session.last_longitude = payload.initial_location.get("longitude")

    return {
        "session_id": session.session_id,
        "preferred_language": session.preferred_language,
        "created_at": session.created_at
    }


@session_router.get("/{session_id}/history", response_model=HistoryResponse, summary="Get conversation history for a session")
async def get_session_history(
    session_id: str = Path(..., description="Unique multi-turn session ID")
):
    """Retrieve full query-response history for multi-turn conversational memory."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    return session.to_history_response()


@session_router.delete("/{session_id}", summary="Delete a session")
async def delete_session(
    session_id: str = Path(..., description="Unique multi-turn session ID")
):
    """Delete session memory and associated context."""
    deleted = session_manager.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    return {"status": "success", "message": f"Session '{session_id}' deleted."}
