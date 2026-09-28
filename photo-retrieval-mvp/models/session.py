"""
models/session.py
Pydantic schemas for session management, API request/response contracts,
and user authentication state.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from models.memory_context import MemoryContext
from models.photo_candidate import CandidateCluster


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SessionOutcome(str, Enum):
    FOUND = "found"
    NOT_FOUND = "not_found"
    ABANDONED = "abandoned"
    ACTIVE = "active"


class FeedbackType(str, Enum):
    YES = "yes"
    NO = "no"
    WARMER = "warmer"


# ---------------------------------------------------------------------------
# Session model
# ---------------------------------------------------------------------------

class Session(BaseModel):
    """Full session object stored in PostgreSQL for logging and analytics."""

    session_id: UUID = Field(default_factory=uuid4)
    user_id: str
    outcome: SessionOutcome = SessionOutcome.ACTIVE
    turn_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None
    found_photo_id: Optional[str] = None  # Set on SessionOutcome.FOUND


# ---------------------------------------------------------------------------
# API Request / Response schemas
# ---------------------------------------------------------------------------

class StartSessionRequest(BaseModel):
    """Request to create a new retrieval session."""
    pass  # user_id is derived from the OAuth token in the auth middleware


class StartSessionResponse(BaseModel):
    """Response after creating a new session."""
    session_id: UUID
    message: str = "Tell me about the photo you're looking for — any detail you remember helps."


class UserMessageRequest(BaseModel):
    """A user's conversational message in an active session."""
    text: str = Field(..., min_length=1, max_length=2000)


class AssistantResponse(BaseModel):
    """
    Response to a user message: the AI's conversational reply,
    updated candidates, and a snapshot of the current context.
    """
    response_text: str = Field(..., description="Conversational reply from the AI")
    clusters: list[CandidateCluster] = Field(
        default_factory=list,
        description="Ranked event clusters to display in the photo grid",
    )
    context_snapshot: Optional[MemoryContext] = Field(
        None,
        description="Current MemoryContext state (for debugging / progressive UI)",
    )
    retrieval_attempted: bool = Field(
        False,
        description="True if a retrieval query was issued this turn",
    )
    needs_more_info: bool = Field(
        True,
        description="True if system is still collecting memory signals",
    )


class FeedbackRequest(BaseModel):
    """User feedback on a specific photo candidate."""
    photo_id: str = Field(..., description="ID of the photo the user is reacting to")
    feedback: FeedbackType


class FeedbackResponse(BaseModel):
    """Updated candidate list after processing feedback."""
    clusters: list[CandidateCluster]
    response_text: str
    session_ended: bool = False


class EndSessionRequest(BaseModel):
    """Explicit session end from the frontend."""
    outcome: SessionOutcome
    found_photo_id: Optional[str] = None


class SessionContextResponse(BaseModel):
    """
    Returns a session's current MemoryContext and message history.
    Used on page reload to restore the conversation.
    """
    session_id: UUID
    context: MemoryContext
    message_history: list[dict] = Field(
        default_factory=list,
        description="Ordered list of {role, text} message objects",
    )
    outcome: SessionOutcome


class SyncStatusResponse(BaseModel):
    """Library indexing status for the authenticated user."""
    total_photos: int
    indexed_photos: int
    last_sync_at: Optional[datetime] = None
    sync_in_progress: bool = False
    index_ready: bool = False

    @property
    def progress_pct(self) -> float:
        if self.total_photos == 0:
            return 0.0
        return round(self.indexed_photos / self.total_photos * 100, 1)
