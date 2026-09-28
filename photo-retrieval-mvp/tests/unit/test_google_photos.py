"""
tests/unit/test_google_photos.py
Unit tests for the Google Photos adapter using mocked HTTP responses.
No real API calls are made.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import httpx

from integrations.google_photos import (
    AccessRevokedError,
    Album,
    DateFilter,
    GooglePhotosAdapter,
    MediaItem,
    OAuthTokens,
    RateLimitError,
    TokenExpiredError,
)


# ── Fixtures ───────────────────────────────────────────────────────────────────

def make_adapter() -> GooglePhotosAdapter:
    return GooglePhotosAdapter(
        client_id="test_client_id",
        client_secret="test_secret",
        redirect_uri="http://localhost:8000/auth/callback",
    )


def make_valid_tokens(expired: bool = False) -> OAuthTokens:
    if expired:
        expires = datetime(2020, 1, 1, tzinfo=timezone.utc)
    else:
        expires = datetime.now(timezone.utc) + timedelta(hours=1)
    return OAuthTokens(
        access_token="access_token_123",
        refresh_token="refresh_token_abc",
        expires_at=expires,
    )


SAMPLE_MEDIA_ITEM = {
    "id": "photo_001",
    "baseUrl": "https://photos.google.com/id/photo_001",
    "filename": "IMG_001.jpg",
    "mimeType": "image/jpeg",
    "mediaMetadata": {
        "creationTime": "2023-08-15T10:30:00Z",
        "width": "4032",
        "height": "3024",
        "photo": {
            "cameraMake": "Apple",
            "cameraModel": "iPhone 14",
            "location": {"latitude": 15.2993, "longitude": 74.1240},
        },
    },
}

SAMPLE_ALBUM = {
    "id": "album_001",
    "title": "Goa Trip 2023",
    "mediaItemsCount": "42",
    "coverPhotoBaseUrl": "https://photos.google.com/id/cover",
}


# ── OAuthTokens ────────────────────────────────────────────────────────────────

class TestOAuthTokens:
    def test_not_expired_when_future(self):
        tokens = make_valid_tokens(expired=False)
        assert not tokens.is_expired

    def test_expired_when_past(self):
        tokens = make_valid_tokens(expired=True)
        assert tokens.is_expired

    def test_expired_with_60s_buffer(self):
        # Expires in 30 seconds — should be considered expired (buffer is 60s)
        expires = datetime.now(timezone.utc) + timedelta(seconds=30)
        tokens = OAuthTokens(
            access_token="x", refresh_token="y", expires_at=expires
        )
        assert tokens.is_expired


# ── MediaItem.from_api_response ────────────────────────────────────────────────

class TestMediaItemFromApiResponse:
    def test_basic_parse(self):
        item = MediaItem.from_api_response(SAMPLE_MEDIA_ITEM)
        assert item.id == "photo_001"
        assert item.filename == "IMG_001.jpg"
        assert item.mime_type == "image/jpeg"
        assert item.latitude == pytest.approx(15.2993)
        assert item.longitude == pytest.approx(74.1240)
        assert item.creation_time is not None
        assert item.creation_time.year == 2023

    def test_missing_gps(self):
        raw = dict(SAMPLE_MEDIA_ITEM)
        raw["mediaMetadata"] = {
            "creationTime": "2023-08-15T10:30:00Z",
            "photo": {},
        }
        item = MediaItem.from_api_response(raw)
        assert item.latitude is None
        assert item.longitude is None

    def test_missing_creation_time(self):
        raw = dict(SAMPLE_MEDIA_ITEM)
        raw["mediaMetadata"] = {"photo": {}}
        item = MediaItem.from_api_response(raw)
        assert item.creation_time is None

    def test_invalid_creation_time(self):
        raw = dict(SAMPLE_MEDIA_ITEM)
        raw["mediaMetadata"] = {"creationTime": "not-a-date", "photo": {}}
        item = MediaItem.from_api_response(raw)
        assert item.creation_time is None


# ── Album.from_api_response ────────────────────────────────────────────────────

class TestAlbumFromApiResponse:
    def test_basic_parse(self):
        album = Album.from_api_response(SAMPLE_ALBUM)
        assert album.id == "album_001"
        assert album.title == "Goa Trip 2023"
        assert album.media_items_count == 42


# ── GooglePhotosAdapter.get_auth_url ──────────────────────────────────────────

class TestGetAuthUrl:
    def test_contains_client_id(self):
        adapter = make_adapter()
        url = adapter.get_auth_url()
        assert "test_client_id" in url
        assert "photoslibrary" in url
        assert "offline" in url

    def test_state_included(self):
        adapter = make_adapter()
        url = adapter.get_auth_url(state="csrf_token_123")
        assert "csrf_token_123" in url


# ── Token exchange / refresh ───────────────────────────────────────────────────

class TestExchangeCode:
    @pytest.mark.asyncio
    async def test_successful_exchange(self):
        adapter = make_adapter()
        mock_response = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 3600,
            "scope": "https://www.googleapis.com/auth/photoslibrary.readonly",
        }
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_resp = MagicMock()
            mock_resp.json.return_value = mock_response
            mock_resp.raise_for_status = MagicMock()
            mock_post.return_value = mock_resp

            tokens = await adapter.exchange_code("auth_code_xyz")
            assert tokens.access_token == "new_access_token"
            assert tokens.refresh_token == "new_refresh_token"
            assert not tokens.is_expired


class TestRefreshTokens:
    @pytest.mark.asyncio
    async def test_successful_refresh(self):
        adapter = make_adapter()
        expired_tokens = make_valid_tokens(expired=True)
        mock_response = {
            "access_token": "refreshed_access_token",
            "expires_in": 3600,
        }
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_resp = MagicMock()
            mock_resp.json.return_value = mock_response
            mock_resp.status_code = 200
            mock_resp.raise_for_status = MagicMock()
            mock_post.return_value = mock_resp

            new_tokens = await adapter.refresh_tokens(expired_tokens)
            # refresh_token should be preserved from original
            assert new_tokens.refresh_token == expired_tokens.refresh_token
            assert new_tokens.access_token == "refreshed_access_token"

    @pytest.mark.asyncio
    async def test_refresh_revoked_raises(self):
        adapter = make_adapter()
        expired_tokens = make_valid_tokens(expired=True)
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 400
            mock_post.return_value = mock_resp

            with pytest.raises(AccessRevokedError):
                await adapter.refresh_tokens(expired_tokens)


# ── get_media_item ─────────────────────────────────────────────────────────────

class TestGetMediaItem:
    @pytest.mark.asyncio
    async def test_returns_media_item(self):
        adapter = make_adapter()
        tokens = make_valid_tokens()
        with patch.object(adapter, "_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = SAMPLE_MEDIA_ITEM
            item = await adapter.get_media_item("user_001", tokens, "photo_001")
            assert item.id == "photo_001"
            assert item.latitude == pytest.approx(15.2993)


# ── validate_photo_ids ─────────────────────────────────────────────────────────

class TestValidatePhotoIds:
    @pytest.mark.asyncio
    async def test_valid_ids_returned(self):
        adapter = make_adapter()
        tokens = make_valid_tokens()
        with patch.object(adapter, "get_media_item", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MediaItem.from_api_response(SAMPLE_MEDIA_ITEM)
            valid = await adapter.validate_photo_ids("user_001", tokens, ["photo_001"])
            assert "photo_001" in valid

    @pytest.mark.asyncio
    async def test_deleted_photo_excluded(self):
        adapter = make_adapter()
        tokens = make_valid_tokens()
        with patch.object(adapter, "get_media_item", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.HTTPStatusError(
                "404", request=MagicMock(), response=MagicMock()
            )
            valid = await adapter.validate_photo_ids("user_001", tokens, ["deleted_photo"])
            assert len(valid) == 0


# ── Date filter ────────────────────────────────────────────────────────────────

class TestDateFilter:
    def test_date_filter_fields(self):
        start = datetime(2023, 6, 1, tzinfo=timezone.utc)
        end = datetime(2023, 8, 31, tzinfo=timezone.utc)
        df = DateFilter(start=start, end=end)
        assert df.start.year == 2023
        assert df.end.month == 8
