"""
core/feedback.py
Feedback module for dynamic session re-ranking.

Architecture reference: architecture.md §7.4
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from core.session_manager import SessionManager
from models.memory_context import MemoryContext
from models.session import SessionOutcome

logger = logging.getLogger(__name__)


class FeedbackModule:
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager

    async def process_feedback(
        self, session_id: UUID | str, photo_id: str, feedback: str
    ) -> Optional[MemoryContext]:
        """
        Process user feedback on a specific photo.
        feedback can be: "yes", "no", "warmer"
        
        Returns the updated MemoryContext, or None if the session was ended.
        """
        context = await self.session_manager.get_context(session_id)
        if not context:
            logger.warning("Feedback received for inactive session %s", session_id)
            return None
            
        await self.session_manager.log_event(
            session_id, "user_feedback", {"photo_id": photo_id, "feedback": feedback}
        )

        if feedback == "yes":
            # Success! End session.
            await self.session_manager.end_session(session_id, SessionOutcome.FOUND, photo_id)
            return None
            
        elif feedback == "no":
            # Down-weight features or explicitly exclude this photo.
            # For MVP, we'll just track it in candidate pool (implicitly excluded from future top ranks)
            # In advanced version, we'd decrease semantic weight if multiple "no"s.
            logger.info("Feedback 'no' for %s in session %s", photo_id, session_id)
            # Reduce semantic confidence slightly as a penalty
            context.confidence.semantic = max(0.0, getattr(context.confidence, "semantic", 1.0) - 0.1)
            
        elif feedback == "warmer":
            # Up-weight semantic features.
            logger.info("Feedback 'warmer' for %s in session %s", photo_id, session_id)
            # Boost semantic confidence
            context.confidence.semantic = min(1.0, getattr(context.confidence, "semantic", 1.0) + 0.2)
            
        else:
            logger.warning("Unknown feedback type: %s", feedback)
            return context
            
        # Update the session with new weights/context
        await self.session_manager.update_context(context)
        return context
