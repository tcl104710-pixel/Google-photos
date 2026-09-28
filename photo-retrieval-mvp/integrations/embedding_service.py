"""
integrations/embedding_service.py
Semantic embedding engine using BGE-M3 (text) and BGE-Visualized (images).

Both models produce 1024-dim vectors in a shared embedding space,
enabling direct cosine similarity between text queries and photo images
without cross-modal bridging.

Architecture reference: architecture.md §5.3
Edge cases handled:
  EC-3.1 (corrupt/unsupported image — CLIP fallback),
  EC-3.3 (burst photos — dedup via similarity),
  EC-3.4 (abstract query — low-confidence detection),
  EC-10.3 (cold container — model loading health check)
"""

from __future__ import annotations

import hashlib
import logging
import os
from enum import Enum
from pathlib import Path
from typing import Optional

import httpx
import numpy as np

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────
BGE_M3_MODEL_ID = "BAAI/bge-m3"
BGE_VIS_MODEL_ID = "BAAI/bge-visualized-m3"
EMBEDDING_DIM = 1024
LOW_SIMILARITY_THRESHOLD = 0.35   # EC-3.4: below this = abstract query
BURST_SIMILARITY_THRESHOLD = 0.95  # EC-3.3: above this = near-duplicate


class EmbeddingSource(str, Enum):
    BGE_VISUALIZED = "bge_visualized"
    CLIP_FALLBACK = "clip_fallback"
    ZERO_VECTOR = "zero_vector"


# ── Lazy model loading ─────────────────────────────────────────────────────────

class _ModelRegistry:
    """Singleton-style lazy loader for heavy ML models (avoids cold-start penalty)."""

    _bge_m3: Optional[object] = None
    _bge_vis: Optional[object] = None
    _clip_model: Optional[object] = None
    _clip_preprocess: Optional[object] = None
    _device: str = "cpu"

    @classmethod
    def set_device(cls, device: str) -> None:
        cls._device = device

    @classmethod
    def get_bge_m3(cls) -> object:
        if cls._bge_m3 is None:
            logger.info("Loading BGE-M3 text model (%s)…", BGE_M3_MODEL_ID)
            try:
                from FlagEmbedding import BGEM3FlagModel  # type: ignore[import]
                cls._bge_m3 = BGEM3FlagModel(
                    BGE_M3_MODEL_ID,
                    use_fp16=(cls._device != "cpu"),
                )
                logger.info("BGE-M3 loaded successfully")
            except ImportError:
                raise RuntimeError(
                    "FlagEmbedding not installed. Run: pip install FlagEmbedding"
                )
        return cls._bge_m3

    @classmethod
    def get_bge_visualized(cls) -> object:
        if cls._bge_vis is None:
            logger.info("Loading BGE-Visualized model (%s)…", BGE_VIS_MODEL_ID)
            try:
                from FlagEmbedding.visual import FlagVisualModel  # type: ignore[import]
                cls._bge_vis = FlagVisualModel(
                    BGE_VIS_MODEL_ID,
                    query_instruction_for_retrieval="",
                )
                logger.info("BGE-Visualized loaded successfully")
            except ImportError:
                raise RuntimeError(
                    "FlagEmbedding[visual] not installed. "
                    "Run: pip install FlagEmbedding[visual]"
                )
        return cls._bge_vis

    @classmethod
    def get_clip(cls) -> tuple[object, object]:
        """EC-3.1 fallback: load CLIP ViT-L/14 only if needed."""
        if cls._clip_model is None:
            try:
                import clip  # type: ignore[import]
                import torch
                device = cls._device
                model, preprocess = clip.load("ViT-L/14", device=device)
                cls._clip_model = model
                cls._clip_preprocess = preprocess
                logger.info("CLIP ViT-L/14 fallback loaded on %s", device)
            except ImportError:
                raise RuntimeError("clip not installed. Run: pip install openai-clip")
        return cls._clip_model, cls._clip_preprocess

    @classmethod
    def is_ready(cls) -> bool:
        """EC-10.3: health check — returns True only when models are loaded."""
        return cls._bge_m3 is not None and cls._bge_vis is not None


# ── Embedding results ──────────────────────────────────────────────────────────

class EmbeddingResult:
    __slots__ = ("vector", "source", "photo_id")

    def __init__(
        self,
        vector: np.ndarray,
        source: EmbeddingSource,
        photo_id: str = "",
    ) -> None:
        self.vector = vector
        self.source = source
        self.photo_id = photo_id

    @property
    def is_zero(self) -> bool:
        return self.source == EmbeddingSource.ZERO_VECTOR

    def normalised(self) -> np.ndarray:
        """Return L2-normalised vector (required for cosine similarity via dot product)."""
        norm = np.linalg.norm(self.vector)
        if norm < 1e-10:
            return self.vector
        return self.vector / norm


# ── Main Embedding Service ─────────────────────────────────────────────────────

class EmbeddingService:
    """
    Provides embed_text() and embed_image() using BGE-M3 and BGE-Visualized.
    Both produce 1024-dim L2-normalised vectors in a shared space.

    Models are loaded lazily on first call (use preload() on startup for
    production to avoid cold-start latency — EC-10.3).
    """

    def __init__(
        self,
        device: str = "cpu",
        cache_dir: Optional[str] = None,
    ) -> None:
        _ModelRegistry.set_device(device)
        self._device = device
        self._cache_dir = Path(cache_dir) if cache_dir else None

    def preload(self) -> None:
        """
        EC-10.3: Eagerly load both models at container startup.
        Call this before accepting traffic. Returns when models are ready.
        """
        _ModelRegistry.get_bge_m3()
        _ModelRegistry.get_bge_visualized()

    def is_ready(self) -> bool:
        return _ModelRegistry.is_ready()

    # ── Text embedding ─────────────────────────────────────────────────────────

    def embed_text(self, text: str) -> np.ndarray:
        """
        Embed a text string using BGE-M3.
        Returns a 1024-dim L2-normalised vector.
        Input is truncated to 512 tokens internally by the model.
        """
        model = _ModelRegistry.get_bge_m3()
        # BGEM3FlagModel.encode returns a dict with 'dense_vecs'
        output = model.encode(  # type: ignore[union-attr]
            [text],
            batch_size=1,
            max_length=512,
            return_dense=True,
            return_sparse=False,
            return_colbert_vecs=False,
        )
        vec = np.array(output["dense_vecs"][0], dtype=np.float32)
        return vec / (np.linalg.norm(vec) + 1e-10)

    def embed_texts_batch(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        """Batch embed multiple texts. Returns (N, 1024) array."""
        model = _ModelRegistry.get_bge_m3()
        output = model.encode(  # type: ignore[union-attr]
            texts,
            batch_size=batch_size,
            max_length=512,
            return_dense=True,
            return_sparse=False,
            return_colbert_vecs=False,
        )
        vecs = np.array(output["dense_vecs"], dtype=np.float32)
        norms = np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-10
        return vecs / norms

    # ── Image embedding ────────────────────────────────────────────────────────

    async def embed_image(
        self,
        base_url: str,
        photo_id: str = "",
    ) -> EmbeddingResult:
        """
        Fetch image from base_url and embed with BGE-Visualized.
        EC-3.1: On failure, falls back to CLIP. If CLIP also fails,
        returns a zero-vector placeholder with source=ZERO_VECTOR.
        """
        image_bytes = await self._fetch_image(base_url)
        if image_bytes is None:
            return EmbeddingResult(
                np.zeros(EMBEDDING_DIM, dtype=np.float32),
                EmbeddingSource.ZERO_VECTOR,
                photo_id,
            )

        # Primary: BGE-Visualized
        try:
            vec = self._embed_image_bge(image_bytes)
            return EmbeddingResult(vec, EmbeddingSource.BGE_VISUALIZED, photo_id)
        except Exception as e:
            logger.warning(
                "BGE-Visualized failed for photo %s: %s — trying CLIP fallback",
                photo_id, e,
            )

        # Fallback: CLIP ViT-L/14 (EC-3.1)
        try:
            vec = self._embed_image_clip(image_bytes)
            return EmbeddingResult(vec, EmbeddingSource.CLIP_FALLBACK, photo_id)
        except Exception as e:
            logger.error(
                "CLIP fallback also failed for photo %s: %s — using zero vector",
                photo_id, e,
            )

        return EmbeddingResult(
            np.zeros(EMBEDDING_DIM, dtype=np.float32),
            EmbeddingSource.ZERO_VECTOR,
            photo_id,
        )

    async def embed_images_batch(
        self,
        items: list[dict],  # list of {photo_id, base_url}
        batch_size: int = 8,
    ) -> list[EmbeddingResult]:
        """
        Embed a batch of images with progress tracking.
        Each item is processed independently so one failure doesn't block the batch.
        """
        results: list[EmbeddingResult] = []
        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]
            for item in batch:
                result = await self.embed_image(
                    item["base_url"], photo_id=item["photo_id"]
                )
                results.append(result)
            logger.info(
                "Embedding progress: %d / %d", i + len(batch), len(items)
            )
        return results

    def _embed_image_bge(self, image_bytes: bytes) -> np.ndarray:
        """Embed raw image bytes with BGE-Visualized."""
        import io
        from PIL import Image  # type: ignore[import]

        model = _ModelRegistry.get_bge_visualized()
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        output = model.encode(images=[img])  # type: ignore[union-attr]
        vec = np.array(output[0], dtype=np.float32)
        return vec / (np.linalg.norm(vec) + 1e-10)

    def _embed_image_clip(self, image_bytes: bytes) -> np.ndarray:
        """Fallback: embed raw image bytes with CLIP ViT-L/14."""
        import io
        import torch
        from PIL import Image  # type: ignore[import]

        model, preprocess = _ModelRegistry.get_clip()
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        tensor = preprocess(img).unsqueeze(0)  # type: ignore[operator]
        with torch.no_grad():
            features = model.encode_image(tensor)  # type: ignore[union-attr]
        vec = features.cpu().numpy().flatten().astype(np.float32)
        # Pad or truncate to EMBEDDING_DIM (CLIP ViT-L/14 = 768-dim)
        if len(vec) < EMBEDDING_DIM:
            vec = np.pad(vec, (0, EMBEDDING_DIM - len(vec)))
        else:
            vec = vec[:EMBEDDING_DIM]
        return vec / (np.linalg.norm(vec) + 1e-10)

    async def _fetch_image(self, url: str) -> Optional[bytes]:
        """Fetch image bytes from a URL with timeout and error handling."""
        # Append display size suffix for Google Photos baseUrls
        display_url = url if url.endswith("=w800") else f"{url}=w800"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(display_url)
                if resp.status_code in (403, 404):
                    logger.warning("Image URL not accessible (status %d): %s", resp.status_code, url)
                    return None
                resp.raise_for_status()
                return resp.content
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            logger.warning("Failed to fetch image %s: %s", url, e)
            return None

    # ── Similarity utilities ───────────────────────────────────────────────────

    @staticmethod
    def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two L2-normalised vectors."""
        return float(np.dot(a, b))

    @staticmethod
    def batch_cosine_similarity(
        query: np.ndarray, candidates: np.ndarray
    ) -> np.ndarray:
        """
        Compute cosine similarity of query against all candidate vectors.
        query: (1024,), candidates: (N, 1024)
        Returns: (N,) similarity scores.
        """
        return candidates @ query

    def is_abstract_query(
        self, query_vec: np.ndarray, candidate_vecs: np.ndarray
    ) -> bool:
        """
        EC-3.4: Return True if query is too abstract to retrieve anything meaningful.
        Triggers when max cosine similarity across all candidates < threshold.
        """
        if len(candidate_vecs) == 0:
            return True
        scores = self.batch_cosine_similarity(query_vec, candidate_vecs)
        return float(np.max(scores)) < LOW_SIMILARITY_THRESHOLD

    def find_near_duplicates(
        self,
        vectors: np.ndarray,
        threshold: float = BURST_SIMILARITY_THRESHOLD,
    ) -> list[list[int]]:
        """
        EC-3.3: Group near-duplicate photos (burst shots) into clusters.
        Returns list of clusters; each cluster is a list of indices.
        Uses greedy union-find approach for efficiency.
        """
        n = len(vectors)
        parent = list(range(n))

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        # Compute pairwise similarities (O(n²) — acceptable for small batches)
        sims = vectors @ vectors.T
        for i in range(n):
            for j in range(i + 1, n):
                if sims[i, j] >= threshold:
                    ri, rj = find(i), find(j)
                    if ri != rj:
                        parent[ri] = rj

        clusters: dict[int, list[int]] = {}
        for i in range(n):
            root = find(i)
            clusters.setdefault(root, []).append(i)

        return list(clusters.values())
