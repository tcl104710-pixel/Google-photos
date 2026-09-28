"""
tests/unit/test_session_manager.py
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from core.session_manager import SessionManager
from models.memory_context import MemoryContext
from models.session import SessionOutcome


@pytest.fixture
def mock_redis():
    return AsyncMock()


class AsyncContextManagerMock:
    def __init__(self, conn):
        self.conn = conn

    async def __aenter__(self):
        return self.conn

    async def __aexit__(self, exc_type, exc, tb):
        pass

@pytest.fixture
def mock_pool():
    from unittest.mock import MagicMock
    pool = MagicMock()
    conn = AsyncMock()
    # Mock context manager for acquire
    pool.acquire.return_value = AsyncContextManagerMock(conn)
    return pool, conn


@pytest.mark.asyncio
async def test_create_session(mock_redis, mock_pool):
    pool, conn = mock_pool
    manager = SessionManager(mock_redis, pool)
    
    ctx = await manager.create_session("user1")
    
    assert ctx.user_id == "user1"
    assert ctx.session_id is not None
    
    mock_redis.setex.assert_called_once()
    conn.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_context(mock_redis, mock_pool):
    pool, conn = mock_pool
    manager = SessionManager(mock_redis, pool)
    
    ctx_mock = MemoryContext(user_id="u1")
    mock_redis.get.return_value = ctx_mock.model_dump_json()
    
    ctx = await manager.get_context(ctx_mock.session_id)
    
    assert ctx is not None
    assert ctx.user_id == "u1"
    assert ctx.session_id == ctx_mock.session_id
    mock_redis.expire.assert_called_once()


@pytest.mark.asyncio
async def test_get_context_not_found(mock_redis, mock_pool):
    pool, conn = mock_pool
    manager = SessionManager(mock_redis, pool)
    
    mock_redis.get.return_value = None
    
    ctx = await manager.get_context("fake_session")
    assert ctx is None


@pytest.mark.asyncio
async def test_update_context(mock_redis, mock_pool):
    pool, conn = mock_pool
    manager = SessionManager(mock_redis, pool)
    
    ctx = MemoryContext(user_id="u1")
    ctx.add_description("test")
    
    await manager.update_context(ctx)
    
    mock_redis.setex.assert_called_once()
    conn.execute.assert_called_once()
    
    # Verify we updated turn count in Postgres
    call_args = conn.execute.call_args[0]
    assert "UPDATE sessions" in call_args[0]
    assert call_args[3] == 1 # turn_count


@pytest.mark.asyncio
async def test_end_session(mock_redis, mock_pool):
    pool, conn = mock_pool
    manager = SessionManager(mock_redis, pool)
    
    await manager.end_session("session_1", SessionOutcome.FOUND, "photo_123")
    
    mock_redis.delete.assert_called_once_with("session:session_1")
    conn.execute.assert_called_once()
    
    call_args = conn.execute.call_args[0]
    assert call_args[1] == SessionOutcome.FOUND.value
    assert call_args[2] == "photo_123"


@pytest.mark.asyncio
async def test_log_event(mock_redis, mock_pool):
    pool, conn = mock_pool
    manager = SessionManager(mock_redis, pool)
    
    await manager.log_event("session_1", "message", {"text": "hello"})
    
    conn.execute.assert_called_once()
    call_args = conn.execute.call_args[0]
    assert call_args[2] == "message"
    assert json.loads(call_args[3]) == {"text": "hello"}
