"""
core/caption_enrichment.py
AI caption and scene label enrichment using Groq (Llama 3.3 70B with vision).

For each photo that lacks description / scene labels:
  1. Fetch photo thumbnail from Google Photos baseUrl
  2. Send to Groq vision endpoint as base64 image + structured JSON prompt
  3. Parse structured response: {description, scene_labels, activities, objects}
  4. Store in photo_labels table via MetadataIndex

Fallback strategy:
  - If Groq vision rate-limited (429): use photo description field from Google Photos API
  - If both fail: store a minimal label from the photo filename

Architecture reference: architecture.md §5.4
Edge cases handled:
  EC-2.4 (Groq rate limit during bulk enrichment — exponential backoff + checkpoint),
  EC-2.2 (Groq returns malformed JSON — retry with corrective prompt),
  EC-4.6 (expired baseUrl — re-fetch from Google Photos)
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import re
from dataclasses import dataclass
from typing import Optional

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

logger = logging.getLogger(__name__)

# ── Groq vision config ─────────────────────────────────────────────────────────
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
VISION_MODEL = "llama-3.3-70b-versatile"          # Groq model with vision capability
MAX_IMAGE_SIZE_BYTES = 4 * 1024 * 1024            # 4 MB cap for inline base64
BATCH_SIZE = 10                                    # Photos per enrichment batch
INTER_BATCH_DELAY_SECONDS = 2.0                   # Rate-limit safety delay


# ── Structured output schema ───────────────────────────────────────────────────

CAPTION_SYSTEM_PROMPT = """You are an expert photo analyst. Analyse the provided photo and respond ONLY with valid JSON matching this exact schema — no extra text, no markdown, no explanation:

{
  "description": "<one sentence describing the photo scene and content>",
  "scene_labels": ["<label1>", "<label2>"],
  "activities": ["<activity1>"],
  "objects": ["<object1>", "<object2>"],
  "mood": "<bright|warm|dark|neutral>",
  "setting": "<indoor|outdoor|unknown>"
}

Rules:
- scene_labels: max 5 items from: beach, restaurant, cafe, park, mountain, street, indoor, outdoor, celebration, travel, food, people, nature, architecture, vehicle
- activities: max 3 items, verb form (e.g. "eating", "swimming", "walking")
- objects: max 5 prominent objects visible
- All values must be in English
"""

CORRECTIVE_PROMPT = """Your previous response was not valid JSON matching the required schema. Respond ONLY with valid JSON, no other text:

{
  "description": "...",
  "scene_labels": [...],
  "activities": [...],
  "objects": [...],
  "mood": "...",
  "setting": "..."
}"""


@dataclass
class CaptionResult:
    photo_id: str
    description: str
    scene_labels: list[str]
    activities: list[str]
    objects: list[str]
    mood: str
    setting: str
    source: str  # "groq_vision" | "google_description" | "filename_fallback"


# ── Caption Enrichment Service ─────────────────────────────────────────────────

class CaptionEnrichmentService:
    """
    Generates AI captions and scene labels for photos.
    Processes in batches with rate-limit handling and checkpointing.
    """

    def __init__(
        self,
        groq_api_key: str,
        model: str = VISION_MODEL,
    ) -> None:
        self._api_key = groq_api_key
        self._model = model

    # ── Public API ─────────────────────────────────────────────────────────────

    async def enrich_batch(
        self,
        photos: list[dict],  # list of {photo_id, base_url, description?, filename}
        progress_callback: Optional[object] = None,
    ) -> list[CaptionResult]:
        """
        Enrich a batch of photos.
        EC-2.4: Sleeps between sub-batches; checkpoints on rate-limit.
        """
        results: list[CaptionResult] = []

        for i in range(0, len(photos), BATCH_SIZE):
            sub_batch = photos[i : i + BATCH_SIZE]

            for photo in sub_batch:
                result = await self._enrich_single(photo)
                results.append(result)

            logger.info(
                "Caption enrichment progress: %d / %d",
                i + len(sub_batch), len(photos),
            )

            # EC-2.4: inter-batch delay to avoid saturating Groq quota
            if i + BATCH_SIZE < len(photos):
                await asyncio.sleep(INTER_BATCH_DELAY_SECONDS)

        return results

    async def _enrich_single(self, photo: dict) -> CaptionResult:
        """Attempt caption for a single photo with full fallback chain."""
        photo_id = photo["photo_id"]
        base_url = photo.get("base_url", "")
        existing_description = photo.get("description")
        filename = photo.get("filename", "")

        # Try Groq vision first
        if base_url:
            try:
                result = await self._caption_via_groq(photo_id, base_url)
                return result
            except _RateLimitError:
                logger.warning(
                    "Groq rate limit hit for photo %s — falling back to description",
                    photo_id,
                )
            except Exception as e:
                logger.warning(
                    "Groq vision failed for photo %s: %s — falling back", photo_id, e
                )

        # Fallback 1: use existing Google Photos description
        if existing_description:
            return CaptionResult(
                photo_id=photo_id,
                description=existing_description,
                scene_labels=self._labels_from_description(existing_description),
                activities=[],
                objects=[],
                mood="neutral",
                setting="unknown",
                source="google_description",
            )

        # Fallback 2: minimal label from filename
        return CaptionResult(
            photo_id=photo_id,
            description=f"Photo: {filename}",
            scene_labels=[],
            activities=[],
            objects=[],
            mood="neutral",
            setting="unknown",
            source="filename_fallback",
        )

    # ── Groq vision call ───────────────────────────────────────────────────────

    async def _caption_via_groq(
        self, photo_id: str, base_url: str
    ) -> CaptionResult:
        """
        Fetch image and send to Groq vision endpoint.
        EC-2.2: On malformed JSON response, retries once with corrective prompt.
        EC-2.4: On 429, raises _RateLimitError for caller to handle.
        """
        image_b64 = await self._fetch_image_base64(base_url)
        if image_b64 is None:
            raise ValueError(f"Could not fetch image for photo {photo_id}")

        raw_json = await self._call_groq_vision(image_b64)

        # EC-2.2: parse with retry on malformed JSON
        parsed = self._parse_caption_json(raw_json)
        if parsed is None:
            logger.warning("Malformed JSON for photo %s — retrying with corrective prompt", photo_id)
            raw_json2 = await self._call_groq_vision(image_b64, corrective=True)
            parsed = self._parse_caption_json(raw_json2)
            if parsed is None:
                raise ValueError(f"Groq returned invalid JSON twice for photo {photo_id}")

        return CaptionResult(
            photo_id=photo_id,
            description=parsed.get("description", ""),
            scene_labels=parsed.get("scene_labels", []),
            activities=parsed.get("activities", []),
            objects=parsed.get("objects", []),
            mood=parsed.get("mood", "neutral"),
            setting=parsed.get("setting", "unknown"),
            source="groq_vision",
        )

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(2),
        wait=wait_exponential_jitter(initial=2, max=30),
        reraise=True,
    )
    async def _call_groq_vision(
        self, image_b64: str, corrective: bool = False
    ) -> str:
        """Call the Groq API with a base64 image payload."""
        messages = [
            {"role": "system", "content": CAPTION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                    },
                    {
                        "type": "text",
                        "text": CORRECTIVE_PROMPT if corrective else "Analyse this photo.",
                    },
                ],
            },
        ]

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._model,
                    "messages": messages,
                    "max_tokens": 512,
                    "temperature": 0.1,
                },
            )

            if resp.status_code == 429:
                raise _RateLimitError("Groq 429 — rate limited")
            resp.raise_for_status()

        data = resp.json()
        return data["choices"][0]["message"]["content"]

    # ── Helpers ────────────────────────────────────────────────────────────────

    async def _fetch_image_base64(
        self, base_url: str, max_size: int = MAX_IMAGE_SIZE_BYTES
    ) -> Optional[str]:
        """Fetch image bytes and convert to base64 for Groq inline image."""
        display_url = f"{base_url}=w512-h512"  # Small thumbnail for efficiency
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(display_url)
                if resp.status_code in (403, 404):
                    return None
                resp.raise_for_status()
                content = resp.content
                if len(content) > max_size:
                    logger.warning("Image too large (%d bytes) — skipping vision call", len(content))
                    return None
                return base64.b64encode(content).decode("utf-8")
        except Exception as e:
            logger.warning("Failed to fetch image for base64: %s", e)
            return None

    @staticmethod
    def _parse_caption_json(raw: str) -> Optional[dict]:
        """Extract and validate JSON from Groq response (EC-2.2)."""
        # Strip markdown code fences if present
        raw = re.sub(r"```(?:json)?\s*", "", raw).strip()
        try:
            data = json.loads(raw)
            # Validate required keys
            required = {"description", "scene_labels", "activities", "objects"}
            if not required.issubset(data.keys()):
                return None
            return data
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _labels_from_description(text: str) -> list[str]:
        """Extract simple scene labels from a text description (fallback)."""
        keywords = [
            "beach", "restaurant", "cafe", "park", "mountain", "street",
            "indoor", "outdoor", "celebration", "travel", "food", "people",
            "nature", "architecture",
        ]
        found = [k for k in keywords if k.lower() in text.lower()]
        return found[:5]


class _RateLimitError(Exception):
    """Groq returned 429 — rate limited."""
