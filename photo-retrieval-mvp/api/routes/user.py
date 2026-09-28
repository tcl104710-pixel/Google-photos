"""
api/routes/user.py
Endpoints for user-specific operations, like checking library sync status.
"""

from fastapi import APIRouter, Depends

from api.dependencies import get_current_user_id, get_pg_pool
from pydantic import BaseModel
import asyncpg

router = APIRouter(prefix="/user", tags=["User"])


class SyncStatusResponse(BaseModel):
    total_photos: int
    indexed_photos: int
    sync_in_progress: bool


@router.get("/sync-status", response_model=SyncStatusResponse)
async def get_sync_status(
    user_id: str = Depends(get_current_user_id),
    pool: asyncpg.Pool = Depends(get_pg_pool),
):
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT total_photos, indexed_photos, sync_in_progress
            FROM library_sync
            WHERE user_id = $1
            """,
            user_id
        )
        
    if not row:
        return SyncStatusResponse(
            total_photos=0,
            indexed_photos=0,
            sync_in_progress=False
        )
        
    return SyncStatusResponse(
        total_photos=row["total_photos"],
        indexed_photos=row["indexed_photos"],
        sync_in_progress=row["sync_in_progress"]
    )
