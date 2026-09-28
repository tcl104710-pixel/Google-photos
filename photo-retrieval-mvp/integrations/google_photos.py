"""
integrations/google_photos.py
Google Photos Library API adapter.

Responsibilities:
  - OAuth 2.0 authorisation URL generation, token exchange, token refresh
  - Paginated retrieval of all media items (list_media_items)
  - Single item metadata fetch (get_media_item)
  - Date-range + content-category search (search_media_items)
  - Album listing (get_albums)
  - Graceful rate-limit handling: exponential backoff + jitter via tenacity
  - Secure token storage in PostgreSQL (via token_store callback)

Architecture reference: architecture.md §5.1, §6
Edge cases handled: EC-4.1 (token expired), EC-4.2 (access revoked),
                    EC-4.5 (daily quota), EC-4.6 (baseUrl expiry)
"""

from __future__ import annotations

import asyncio
import logging
import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Callable, Optional

import httpx
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
)

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_REVOKE_URL = "https://oauth2.googleapis.com/revoke"
PHOTOS_BASE_URL = "https://photoslibrary.googleapis.com/v1"
SCOPES = ["https://www.googleapis.com/auth/photoslibrary.readonly"]

DEFAULT_PAGE_SIZE = 50        # Google max is 100
MAX_PAGES_PER_SYNC = 200      # Safety cap; ~10,000 photos per sync call
BASE_URL_TTL_SECONDS = 3600   # Google Photos baseUrl expires in 60 minutes


# ── Data structures ────────────────────────────────────────────────────────────

@dataclass
class OAuthTokens:
    access_token: str
    refresh_token: str
    expires_at: datetime
    scope: str = ""

    @property
    def is_expired(self) -> bool:
        # Treat as expired 60s before actual expiry (safety buffer)
        now = datetime.now(timezone.utc)
        expires = self.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return (expires - now).total_seconds() < 60


@dataclass
class MediaItem:
    """Single Google Photos media item."""
    id: str
    base_url: str
    filename: str
    mime_type: str
    creation_time: Optional[datetime]
    width: Optional[int]
    height: Optional[int]
    camera_make: Optional[str]
    camera_model: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    description: Optional[str]
    album_ids: list[str] = field(default_factory=list)

    @classmethod
    def from_api_response(cls, item: dict[str, Any]) -> "MediaItem":
        meta = item.get("mediaMetadata", {})
        photo_meta = meta.get("photo", {})
        loc = photo_meta.get("location", {})
        creation_raw = meta.get("creationTime")
        creation_dt: Optional[datetime] = None
        if creation_raw:
            try:
                creation_dt = datetime.fromisoformat(
                    creation_raw.replace("Z", "+00:00")
                )
            except ValueError:
                pass

        return cls(
            id=item["id"],
            base_url=item.get("baseUrl", ""),
            filename=item.get("filename", ""),
            mime_type=item.get("mimeType", ""),
            creation_time=creation_dt,
            width=int(meta.get("width", 0)) or None,
            height=int(meta.get("height", 0)) or None,
            camera_make=photo_meta.get("cameraMake"),
            camera_model=photo_meta.get("cameraModel"),
            latitude=loc.get("latitude"),
            longitude=loc.get("longitude"),
            description=item.get("description"),
        )


@dataclass
class Album:
    id: str
    title: str
    media_items_count: int
    cover_photo_base_url: Optional[str]

    @classmethod
    def from_api_response(cls, a: dict[str, Any]) -> "Album":
        return cls(
            id=a["id"],
            title=a.get("title", ""),
            media_items_count=int(a.get("mediaItemsCount", 0)),
            cover_photo_base_url=a.get("coverPhotoBaseUrl"),
        )


@dataclass
class DateFilter:
    start: datetime
    end: datetime


# ── Exception helpers ──────────────────────────────────────────────────────────

class GooglePhotosError(Exception):
    """Base error for Google Photos adapter."""

class TokenExpiredError(GooglePhotosError):
    """OAuth access token has expired and cannot be refreshed."""

class AccessRevokedError(GooglePhotosError):
    """User has revoked app access. Stop all API calls immediately."""

class RateLimitError(GooglePhotosError):
    """Daily quota or per-minute rate limit exceeded."""


def _is_retryable(exc: BaseException) -> bool:
    """Retry on 5xx and rate-limit (429) responses."""
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in (429, 500, 502, 503, 504)
    if isinstance(exc, (httpx.TimeoutException, httpx.ConnectError)):
        return True
    return False


# ── Main Adapter ──────────────────────────────────────────────────────────────

class GooglePhotosAdapter:
    """
    Async adapter for the Google Photos Library REST API.

    Usage:
        adapter = GooglePhotosAdapter(
            client_id=..., client_secret=..., redirect_uri=...
        )
        tokens = await adapter.exchange_code(code)
        async for item in adapter.list_media_items(tokens):
            process(item)
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        page_size: int = DEFAULT_PAGE_SIZE,
        # Optional callback: called whenever tokens are refreshed so the
        # caller can persist them to PostgreSQL
        on_token_refresh: Optional[Callable[[str, OAuthTokens], None]] = None,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.page_size = page_size
        self.on_token_refresh = on_token_refresh

    # ── OAuth helpers ──────────────────────────────────────────────────────────

    def get_auth_url(self, state: str = "") -> str:
        """Generate the Google OAuth authorisation URL for the user to visit."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        return f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"

    async def exchange_code(self, code: str) -> OAuthTokens:
        """Exchange an authorisation code for access + refresh tokens."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "redirect_uri": self.redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            resp.raise_for_status()
            return self._parse_token_response(resp.json())

    async def refresh_tokens(self, tokens: OAuthTokens) -> OAuthTokens:
        """Refresh an expired access token using the refresh token."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "refresh_token": tokens.refresh_token,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "refresh_token",
                },
            )
            if resp.status_code == 400:
                # refresh_token is invalid/revoked
                raise AccessRevokedError(
                    "Refresh token rejected — user has revoked app access"
                )
            resp.raise_for_status()
            data = resp.json()
            # Google may not return a new refresh_token; keep the old one
            new_tokens = self._parse_token_response(data)
            if not new_tokens.refresh_token:
                new_tokens.refresh_token = tokens.refresh_token
            return new_tokens

    def _parse_token_response(self, data: dict[str, Any]) -> OAuthTokens:
        import time
        expires_in = int(data.get("expires_in", 3600))
        expires_at = datetime.fromtimestamp(
            time.time() + expires_in, tz=timezone.utc
        )
        return OAuthTokens(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token", ""),
            expires_at=expires_at,
            scope=data.get("scope", ""),
        )

    async def _ensure_valid_token(
        self, user_id: str, tokens: OAuthTokens
    ) -> OAuthTokens:
        """EC-4.1: auto-refresh token if expired before making any API call."""
        if tokens.is_expired:
            logger.info("Access token expired for user %s — refreshing", user_id)
            tokens = await self.refresh_tokens(tokens)
            if self.on_token_refresh:
                self.on_token_refresh(user_id, tokens)
        return tokens

    # ── HTTP helper with retry + auth ──────────────────────────────────────────

    async def _get(
        self,
        user_id: str,
        tokens: OAuthTokens,
        url: str,
        params: Optional[dict] = None,
    ) -> dict[str, Any]:
        tokens = await self._ensure_valid_token(user_id, tokens)

        @retry(
            retry=retry_if_exception(_is_retryable),
            stop=stop_after_attempt(3),
            wait=wait_exponential_jitter(initial=1, max=30),
            reraise=True,
        )
        async def _call() -> dict[str, Any]:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    url,
                    headers={"Authorization": f"Bearer {tokens.access_token}"},
                    params=params or {},
                )
                if resp.status_code == 401:
                    raise TokenExpiredError("401 — token rejected")
                if resp.status_code == 403:
                    raise AccessRevokedError("403 — access revoked")
                if resp.status_code == 429:
                    retry_after = int(resp.headers.get("Retry-After", 60))
                    logger.warning(
                        "Rate limited for user %s; retry after %ss",
                        user_id, retry_after,
                    )
                    await asyncio.sleep(retry_after)
                    raise RateLimitError("429 — quota exceeded")
                resp.raise_for_status()
                return resp.json()  # type: ignore[return-value]

        return await _call()

    async def _post(
        self,
        user_id: str,
        tokens: OAuthTokens,
        url: str,
        body: dict[str, Any],
    ) -> dict[str, Any]:
        tokens = await self._ensure_valid_token(user_id, tokens)

        @retry(
            retry=retry_if_exception(_is_retryable),
            stop=stop_after_attempt(3),
            wait=wait_exponential_jitter(initial=1, max=30),
            reraise=True,
        )
        async def _call() -> dict[str, Any]:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {tokens.access_token}",
                        "Content-Type": "application/json",
                    },
                    json=body,
                )
                if resp.status_code == 401:
                    raise TokenExpiredError("401 — token rejected")
                if resp.status_code == 403:
                    raise AccessRevokedError("403 — access revoked")
                if resp.status_code == 429:
                    retry_after = int(resp.headers.get("Retry-After", 60))
                    await asyncio.sleep(retry_after)
                    raise RateLimitError("429 — quota exceeded")
                resp.raise_for_status()
                return resp.json()  # type: ignore[return-value]

        return await _call()

    # ── Public API methods ─────────────────────────────────────────────────────

    async def list_media_items(
        self,
        user_id: str,
        tokens: OAuthTokens,
        page_token: Optional[str] = None,
        max_pages: int = MAX_PAGES_PER_SYNC,
    ) -> AsyncIterator[tuple[MediaItem, Optional[str]]]:
        """
        Paginated retrieval of all photos.
        Yields (MediaItem, next_page_token) tuples.
        next_page_token is None on the last page.

        EC-4.5: Caller should checkpoint page_token on RateLimitError.
        """
        current_token = page_token
        pages_fetched = 0

        while pages_fetched < max_pages:
            params: dict[str, Any] = {"pageSize": self.page_size}
            if current_token:
                params["pageToken"] = current_token

            data = await self._get(
                user_id, tokens, f"{PHOTOS_BASE_URL}/mediaItems", params
            )
            items = data.get("mediaItems", [])
            next_token: Optional[str] = data.get("nextPageToken")

            for raw in items:
                yield MediaItem.from_api_response(raw), next_token

            if not next_token:
                break

            current_token = next_token
            pages_fetched += 1

    async def get_media_item(
        self,
        user_id: str,
        tokens: OAuthTokens,
        media_item_id: str,
    ) -> MediaItem:
        """Fetch a single photo's metadata (used to refresh baseUrl — EC-4.6)."""
        data = await self._get(
            user_id, tokens, f"{PHOTOS_BASE_URL}/mediaItems/{media_item_id}"
        )
        return MediaItem.from_api_response(data)

    async def search_media_items(
        self,
        user_id: str,
        tokens: OAuthTokens,
        date_filter: Optional[DateFilter] = None,
        content_categories: Optional[list[str]] = None,
        page_token: Optional[str] = None,
    ) -> AsyncIterator[tuple[MediaItem, Optional[str]]]:
        """
        Search photos by date range and/or content category.
        Content categories: LANDSCAPES, PEOPLE, PETS, TRAVEL, WEDDINGS, etc.
        """
        body: dict[str, Any] = {"pageSize": self.page_size}
        filters: dict[str, Any] = {}

        if date_filter:
            filters["dateFilter"] = {
                "ranges": [{
                    "startDate": {
                        "year": date_filter.start.year,
                        "month": date_filter.start.month,
                        "day": date_filter.start.day,
                    },
                    "endDate": {
                        "year": date_filter.end.year,
                        "month": date_filter.end.month,
                        "day": date_filter.end.day,
                    },
                }]
            }

        if content_categories:
            filters["contentFilter"] = {
                "includedContentCategories": content_categories
            }

        if filters:
            body["filters"] = filters
        if page_token:
            body["pageToken"] = page_token

        while True:
            data = await self._post(
                user_id, tokens, f"{PHOTOS_BASE_URL}/mediaItems:search", body
            )
            items = data.get("mediaItems", [])
            next_token: Optional[str] = data.get("nextPageToken")

            for raw in items:
                yield MediaItem.from_api_response(raw), next_token

            if not next_token:
                break
            body["pageToken"] = next_token

    async def get_albums(
        self,
        user_id: str,
        tokens: OAuthTokens,
    ) -> list[Album]:
        """Retrieve all albums for the authenticated user."""
        albums: list[Album] = []
        params: dict[str, Any] = {"pageSize": 50}

        while True:
            data = await self._get(
                user_id, tokens, f"{PHOTOS_BASE_URL}/albums", params
            )
            for raw in data.get("albums", []):
                albums.append(Album.from_api_response(raw))

            next_token: Optional[str] = data.get("nextPageToken")
            if not next_token:
                break
            params["pageToken"] = next_token

        return albums

    async def get_fresh_base_url(
        self,
        user_id: str,
        tokens: OAuthTokens,
        media_item_id: str,
    ) -> str:
        """
        EC-4.6: Refresh an expired baseUrl by re-fetching the media item metadata.
        Returns the fresh baseUrl with =w1920-h1080 suffix for display.
        """
        item = await self.get_media_item(user_id, tokens, media_item_id)
        return item.base_url

    async def validate_photo_ids(
        self,
        user_id: str,
        tokens: OAuthTokens,
        photo_ids: list[str],
    ) -> set[str]:
        """
        EC-9.3: Validate that photo IDs still exist in the user's library.
        Returns the set of valid (still-existing) photo IDs.
        """
        valid: set[str] = set()
        for pid in photo_ids:
            try:
                await self.get_media_item(user_id, tokens, pid)
                valid.add(pid)
            except (httpx.HTTPStatusError, GooglePhotosError):
                logger.warning("Photo %s no longer accessible for user %s", pid, user_id)
        return valid
