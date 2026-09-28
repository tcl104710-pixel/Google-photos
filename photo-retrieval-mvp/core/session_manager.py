"""
core/session_manager.py
Session state management using Redis for fast active-session storage
and PostgreSQL for durable event logging.

Architecture reference: architecture.md §6.4
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

import asyncpg
from redis.asyncio import Redis

from models.memory_context import MemoryContext
from models.session import SessionOutcome

logger = logging.getLogger(__name__)

SESSION_TTL = 3600  # 1 hour


class SessionManager:
    def __init__(self, redis: Redis, pool: asyncpg.Pool):
        self.redis = redis
        self.pool = pool

    def _redis_key(self, session_id: UUID | str) -> str:
        return f"session:{str(session_id)}"

    async def create_session(self, user_id: str) -> MemoryContext:
        """Create a new session, store in Redis and Postgres."""
        session_id = uuid4()
        context = MemoryContext(session_id=session_id, user_id=user_id)
        
        # Save to Redis
        await self.redis.setex(
            self._redis_key(session_id),
            SESSION_TTL,
            context.model_dump_json(),
        )
        
        # Log to Postgres
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO sessions (session_id, user_id, outcome, context_snapshot, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                session_id,
                user_id,
                SessionOutcome.ACTIVE.value,
                context.model_dump_json(),
                datetime.now(timezone.utc),
                datetime.now(timezone.utc),
            )
            
        return context

    async def get_context(self, session_id: UUID | str) -> Optional[MemoryContext]:
        """Fetch active session context from Redis."""
        data = await self.redis.get(self._redis_key(session_id))
        if not data:
            return None
            
        # Refresh TTL
        await self.redis.expire(self._redis_key(session_id), SESSION_TTL)
        return MemoryContext.model_validate_json(data)

    async def update_context(self, context: MemoryContext) -> None:
        """Update active session context in Redis and checkpoint to Postgres."""
        session_id = context.session_id
        
        # Save to Redis
        await self.redis.setex(
            self._redis_key(session_id),
            SESSION_TTL,
            context.model_dump_json(),
        )
        
        # Checkpoint to Postgres
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE sessions 
                SET context_snapshot = $1::jsonb, updated_at = $2, turn_count = $3
                WHERE session_id = $4
                """,
                context.model_dump_json(),
                datetime.now(timezone.utc),
                context.turn_count,
                session_id,
            )

    async def end_session(
        self, session_id: UUID | str, outcome: SessionOutcome, found_photo_id: Optional[str] = None
    ) -> None:
        """End a session, remove from Redis, update Postgres outcome."""
        await self.redis.delete(self._redis_key(session_id))
        
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE sessions 
                SET outcome = $1, found_photo_id = $2, ended_at = $3, updated_at = $3
                WHERE session_id = $4
                """,
                outcome.value,
                found_photo_id,
                datetime.now(timezone.utc),
                session_id,
            )

    async def log_event(self, session_id: UUID | str, event_type: str, payload: dict) -> None:
        """Log a session event to Postgres for analytics."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO session_events (session_id, event_type, payload, created_at)
                VALUES ($1, $2, $3::jsonb, $4)
                """,
                session_id,
                event_type,
                json.dumps(payload),
                datetime.now(timezone.utc),
            )
