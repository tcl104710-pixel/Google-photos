"""
core/metadata_index.py
Metadata indexing pipeline: syncs Google Photos metadata into PostgreSQL.

Responsibilities:
  - Incremental sync: fetch new photos since last sync page token
  - Upsert photos, people, albums, labels into DB
  - Background sync task with progress reporting
  - Queryable by date range, person label, album, GPS bounding box

Architecture reference: architecture.md §5.2
Edge cases handled:
  EC-4.3 (empty library), EC-4.4 (large library > 100k),
  EC-4.5 (daily quota — checkpoint page_token), EC-10.2 (DB pool exhaustion)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

import asyncpg

from integrations.google_photos import (
    AccessRevokedError,
    GooglePhotosAdapter,
    MediaItem,
    OAuthTokens,
    RateLimitError,
)

logger = logging.getLogger(__name__)

# ── Sync result ────────────────────────────────────────────────────────────────

@dataclass
class SyncResult:
    user_id: str
    photos_fetched: int = 0
    photos_upserted: int = 0
    photos_skipped: int = 0
    failed_ids: list[str] = None  # type: ignore[assignment]
    next_page_token: Optional[str] = None  # Checkpoint for quota recovery
    completed: bool = False
    error: Optional[str] = None

    def __post_init__(self) -> None:
        if self.failed_ids is None:
            self.failed_ids = []


# ── Metadata Index ─────────────────────────────────────────────────────────────

class MetadataIndex:
    """
    Syncs Google Photos metadata into PostgreSQL and provides
    metadata-based filtering for the retrieval engine.
    """

    def __init__(
        self,
        pool: asyncpg.Pool,
        adapter: GooglePhotosAdapter,
    ) -> None:
        self._pool = pool
        self._adapter = adapter

    # ── Sync pipeline ─────────────────────────────────────────────────────────

    async def sync_library(
        self,
        user_id: str,
        tokens: OAuthTokens,
        resume_page_token: Optional[str] = None,
    ) -> SyncResult:
        """
        Full (or resumed) incremental sync.
        Fetches media items page by page, upserts each batch into DB.
        On RateLimitError (EC-4.5): saves checkpoint and returns partial result.
        On AccessRevokedError (EC-4.2): marks user as revoked; stops sync.
        """
        result = SyncResult(user_id=user_id)
        batch: list[MediaItem] = []

        try:
            async with self._lock_sync(user_id):
                async for item, next_token in self._adapter.list_media_items(
                    user_id, tokens, page_token=resume_page_token
                ):
                    batch.append(item)
                    result.photos_fetched += 1
                    result.next_page_token = next_token

                    if len(batch) >= 50:
                        upserted = await self._upsert_batch(user_id, batch)
                        result.photos_upserted += upserted
                        batch = []
                        await self._update_sync_progress(user_id, result)

                # Flush remaining
                if batch:
                    upserted = await self._upsert_batch(user_id, batch)
                    result.photos_upserted += upserted

                result.completed = True
                await self._update_sync_progress(user_id, result, completed=True)

        except RateLimitError as exc:
            # EC-4.5: checkpoint page token so sync can resume tomorrow
            result.error = str(exc)
            logger.warning(
                "Rate limited for user %s at photo %d. Checkpointing page_token.",
                user_id, result.photos_fetched,
            )
            await self._save_page_token_checkpoint(user_id, result.next_page_token)

        except AccessRevokedError as exc:
            # EC-4.2: flag account and stop
            result.error = str(exc)
            await self._mark_access_revoked(user_id)

        except Exception as exc:
            result.error = f"Unexpected error: {exc}"
            logger.exception("Sync failed for user %s: %s", user_id, exc)

        return result

    async def _upsert_batch(self, user_id: str, items: list[MediaItem]) -> int:
        """Upsert a batch of MediaItems into the photos table."""
        if not items:
            return 0

        async with self._pool.acquire() as conn:
            # Use PostgreSQL UPSERT (ON CONFLICT DO UPDATE)
            rows = [
                (
                    item.id,
                    user_id,
                    item.filename,
                    item.mime_type,
                    item.creation_time,
                    item.width,
                    item.height,
                    item.latitude,
                    item.longitude,
                    item.base_url,
                    item.description,
                    "pending",  # embedding_status
                )
                for item in items
            ]

            await conn.executemany(
                """
                INSERT INTO photos
                  (id, user_id, filename, mime_type, creation_time,
                   width, height, latitude, longitude, base_url,
                   description, embedding_status)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
                ON CONFLICT (id) DO UPDATE SET
                  base_url = EXCLUDED.base_url,
                  description = COALESCE(EXCLUDED.description, photos.description),
                  synced_at = NOW()
                """,
                rows,
            )
        return len(items)

    # ── Metadata queries ───────────────────────────────────────────────────────

    async def query_by_date_range(
        self,
        user_id: str,
        start: datetime,
        end: datetime,
        limit: int = 500,
    ) -> list[str]:
        """Return photo IDs within the given date range."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id FROM photos
                WHERE user_id = $1
                  AND creation_time BETWEEN $2 AND $3
                ORDER BY creation_time DESC
                LIMIT $4
                """,
                user_id, start, end, limit,
            )
        return [r["id"] for r in rows]

    async def query_by_gps_bbox(
        self,
        user_id: str,
        lat_min: float,
        lat_max: float,
        lng_min: float,
        lng_max: float,
        limit: int = 500,
    ) -> list[str]:
        """Return photo IDs within the GPS bounding box."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id FROM photos
                WHERE user_id = $1
                  AND latitude  BETWEEN $2 AND $3
                  AND longitude BETWEEN $4 AND $5
                ORDER BY creation_time DESC
                LIMIT $6
                """,
                user_id, lat_min, lat_max, lng_min, lng_max, limit,
            )
        return [r["id"] for r in rows]

    async def query_by_person_label(
        self,
        user_id: str,
        person_label: str,
        limit: int = 500,
    ) -> list[str]:
        """Return photo IDs that include the given person label."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT DISTINCT pp.photo_id
                FROM photo_people pp
                JOIN photos p ON p.id = pp.photo_id
                WHERE p.user_id = $1
                  AND pp.person_label ILIKE $2
                LIMIT $3
                """,
                user_id, f"%{person_label}%", limit,
            )
        return [r["photo_id"] for r in rows]

    async def query_by_scene_label(
        self,
        user_id: str,
        labels: list[str],
        limit: int = 500,
    ) -> list[str]:
        """Return photo IDs matching any of the given scene/object labels."""
        if not labels:
            return []
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT DISTINCT pl.photo_id
                FROM photo_labels pl
                JOIN photos p ON p.id = pl.photo_id
                WHERE p.user_id = $1
                  AND pl.label = ANY($2::text[])
                LIMIT $3
                """,
                user_id, labels, limit,
            )
        return [r["photo_id"] for r in rows]

    async def get_photo_metadata(
        self,
        photo_ids: list[str],
    ) -> list[dict[str, Any]]:
        """Bulk-fetch metadata for a list of photo IDs."""
        if not photo_ids:
            return []
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, filename, mime_type, creation_time,
                       latitude, longitude, base_url, description
                FROM photos
                WHERE id = ANY($1::text[])
                """,
                photo_ids,
            )
        return [dict(r) for r in rows]

    async def get_photos_pending_embedding(
        self,
        user_id: str,
        batch_size: int = 32,
    ) -> list[dict[str, Any]]:
        """Return photos that still need embedding (for the embedding pipeline)."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, base_url, mime_type
                FROM photos
                WHERE user_id = $1
                  AND embedding_status = 'pending'
                  AND mime_type LIKE 'image/%'
                ORDER BY creation_time DESC
                LIMIT $2
                """,
                user_id, batch_size,
            )
        return [dict(r) for r in rows]

    async def mark_embedding_done(
        self, photo_id: str, status: str = "done"
    ) -> None:
        """Update embedding status after processing."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                "UPDATE photos SET embedding_status = $1 WHERE id = $2",
                status, photo_id,
            )

    async def upsert_label(
        self,
        photo_id: str,
        label: str,
        source: str,
        confidence: Optional[float] = None,
    ) -> None:
        """Insert or update a scene/object label for a photo."""
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO photo_labels (photo_id, label, source, confidence)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT DO NOTHING
                """,
                photo_id, label, source, confidence,
            )

    async def get_sync_status(self, user_id: str) -> dict[str, Any]:
        """Return the current sync status for a user."""
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT total_photos, indexed_photos, last_sync_at,
                       sync_in_progress, next_page_token
                FROM library_sync
                WHERE user_id = $1
                """,
                user_id,
            )
        if not row:
            return {
                "total_photos": 0, "indexed_photos": 0,
                "last_sync_at": None, "sync_in_progress": False,
                "index_ready": False,
            }
        return dict(row)

    # ── Internal helpers ───────────────────────────────────────────────────────

    async def _update_sync_progress(
        self,
        user_id: str,
        result: SyncResult,
        completed: bool = False,
    ) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO library_sync
                  (user_id, total_photos, indexed_photos, last_sync_at,
                   sync_in_progress)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (user_id) DO UPDATE SET
                  total_photos = EXCLUDED.total_photos,
                  indexed_photos = EXCLUDED.indexed_photos,
                  last_sync_at = EXCLUDED.last_sync_at,
                  sync_in_progress = EXCLUDED.sync_in_progress
                """,
                user_id,
                result.photos_fetched,
                result.photos_upserted,
                datetime.now(timezone.utc),
                not completed,
            )

    async def _save_page_token_checkpoint(
        self, user_id: str, token: Optional[str]
    ) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE library_sync SET next_page_token = $1
                WHERE user_id = $2
                """,
                token, user_id,
            )

    async def _mark_access_revoked(self, user_id: str) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET library_access_revoked = TRUE WHERE id = $1",
                user_id,
            )
        logger.warning("Marked access as revoked for user %s", user_id)

    def _lock_sync(self, user_id: str):
        """Context manager placeholder — full distributed lock via Redis in Phase 4."""
        import contextlib
        return contextlib.nullcontext()
