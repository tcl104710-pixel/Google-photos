"""
tests/unit/test_caption_enrichment.py
Unit tests for CaptionEnrichmentService.
All Groq API calls and HTTP fetches are mocked.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.caption_enrichment import (
    CaptionEnrichmentService,
    CaptionResult,
    _RateLimitError,
)


def make_service() -> CaptionEnrichmentService:
    return CaptionEnrichmentService(groq_api_key="test_key")


VALID_GROQ_RESPONSE = json.dumps({
    "description": "A group of people sitting at a small cafe near the beach",
    "scene_labels": ["cafe", "beach", "outdoor"],
    "activities": ["sitting", "eating"],
    "objects": ["table", "chairs", "food"],
    "mood": "warm",
    "setting": "outdoor",
})


# ── _parse_caption_json ────────────────────────────────────────────────────────

class TestParseCaptionJson:
    def test_valid_json_parsed(self):
        result = CaptionEnrichmentService._parse_caption_json(VALID_GROQ_RESPONSE)
        assert result is not None
        assert result["description"].startswith("A group")
        assert "cafe" in result["scene_labels"]

    def test_json_with_code_fences(self):
        fenced = f"```json\n{VALID_GROQ_RESPONSE}\n```"
        result = CaptionEnrichmentService._parse_caption_json(fenced)
        assert result is not None
        assert result["mood"] == "warm"

    def test_missing_required_field_returns_none(self):
        bad = json.dumps({"description": "ok"})  # Missing scene_labels, activities, objects
        result = CaptionEnrichmentService._parse_caption_json(bad)
        assert result is None

    def test_invalid_json_returns_none(self):
        result = CaptionEnrichmentService._parse_caption_json("{not valid json}")
        assert result is None

    def test_empty_string_returns_none(self):
        result = CaptionEnrichmentService._parse_caption_json("")
        assert result is None


# ── _labels_from_description ───────────────────────────────────────────────────

class TestLabelsFromDescription:
    def test_finds_matching_keywords(self):
        text = "We went to the beach and then had food at a restaurant"
        labels = CaptionEnrichmentService._labels_from_description(text)
        assert "beach" in labels
        assert "restaurant" in labels
        assert "food" in labels

    def test_no_keywords_returns_empty(self):
        labels = CaptionEnrichmentService._labels_from_description("No relevant content here at all")
        assert labels == []

    def test_max_5_labels(self):
        text = "beach restaurant cafe park mountain street indoor outdoor celebration travel"
        labels = CaptionEnrichmentService._labels_from_description(text)
        assert len(labels) <= 5

    def test_case_insensitive(self):
        labels = CaptionEnrichmentService._labels_from_description("We visited BEACH")
        assert "beach" in labels


# ── _enrich_single ─────────────────────────────────────────────────────────────

class TestEnrichSingle:
    @pytest.mark.asyncio
    async def test_groq_vision_success(self):
        svc = make_service()
        photo = {
            "photo_id": "p001",
            "base_url": "https://photos.google.com/id/p001",
            "filename": "IMG_001.jpg",
        }
        with (
            patch.object(svc, "_fetch_image_base64", new_callable=AsyncMock) as mock_fetch,
            patch.object(svc, "_call_groq_vision", new_callable=AsyncMock) as mock_groq,
        ):
            mock_fetch.return_value = "base64encodedimage=="
            mock_groq.return_value = VALID_GROQ_RESPONSE

            result = await svc._enrich_single(photo)
            assert result.source == "groq_vision"
            assert "cafe" in result.scene_labels
            assert result.photo_id == "p001"

    @pytest.mark.asyncio
    async def test_falls_back_to_google_description(self):
        svc = make_service()
        photo = {
            "photo_id": "p002",
            "base_url": "https://photos.google.com/id/p002",
            "description": "A sunset at Goa beach",
            "filename": "IMG_002.jpg",
        }
        with patch.object(svc, "_fetch_image_base64", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None  # Image fetch fails -> no Groq call

            result = await svc._enrich_single(photo)
            assert result.source == "google_description"
            assert result.description == "A sunset at Goa beach"
            assert "beach" in result.scene_labels  # Extracted from description

    @pytest.mark.asyncio
    async def test_falls_back_to_filename(self):
        svc = make_service()
        photo = {
            "photo_id": "p003",
            "base_url": "",
            "filename": "IMG_003.jpg",
        }
        result = await svc._enrich_single(photo)
        assert result.source == "filename_fallback"
        assert "IMG_003.jpg" in result.description

    @pytest.mark.asyncio
    async def test_corrective_prompt_on_malformed_json(self):
        svc = make_service()
        photo = {
            "photo_id": "p004",
            "base_url": "https://photos.google.com/id/p004",
            "filename": "IMG_004.jpg",
        }
        with (
            patch.object(svc, "_fetch_image_base64", new_callable=AsyncMock) as mock_fetch,
            patch.object(svc, "_call_groq_vision", new_callable=AsyncMock) as mock_groq,
        ):
            mock_fetch.return_value = "base64=="
            # First call returns bad JSON, second returns valid
            mock_groq.side_effect = ["{bad json}", VALID_GROQ_RESPONSE]

            result = await svc._enrich_single(photo)
            assert result.source == "groq_vision"
            assert mock_groq.call_count == 2  # Corrective prompt was triggered

    @pytest.mark.asyncio
    async def test_rate_limit_falls_back_to_description(self):
        svc = make_service()
        photo = {
            "photo_id": "p005",
            "base_url": "https://photos.google.com/id/p005",
            "description": "Beach photo",
            "filename": "IMG_005.jpg",
        }
        with (
            patch.object(svc, "_fetch_image_base64", new_callable=AsyncMock) as mock_fetch,
            patch.object(
                svc, "_call_groq_vision",
                new_callable=AsyncMock,
                side_effect=_RateLimitError("429"),
            ),
        ):
            mock_fetch.return_value = "base64=="
            result = await svc._enrich_single(photo)
            # Rate limited → should fall back to Google description
            assert result.source == "google_description"


# ── CaptionResult ──────────────────────────────────────────────────────────────

class TestCaptionResult:
    def test_fields_accessible(self):
        r = CaptionResult(
            photo_id="p1",
            description="A nice beach photo",
            scene_labels=["beach", "outdoor"],
            activities=["swimming"],
            objects=["waves", "sand"],
            mood="bright",
            setting="outdoor",
            source="groq_vision",
        )
        assert r.photo_id == "p1"
        assert len(r.scene_labels) == 2
        assert r.mood == "bright"
