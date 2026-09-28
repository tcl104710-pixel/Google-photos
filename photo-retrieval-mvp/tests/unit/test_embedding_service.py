"""
tests/unit/test_embedding_service.py
Unit tests for EmbeddingService and VectorStore.
All heavy ML models are mocked — no actual model loading occurs.
"""

from __future__ import annotations

import numpy as np
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from integrations.embedding_service import (
    EMBEDDING_DIM,
    EmbeddingResult,
    EmbeddingService,
    EmbeddingSource,
    LOW_SIMILARITY_THRESHOLD,
    BURST_SIMILARITY_THRESHOLD,
)


# ── EmbeddingResult ────────────────────────────────────────────────────────────

class TestEmbeddingResult:
    def test_normalised_returns_unit_vector(self):
        vec = np.array([3.0, 4.0, 0.0], dtype=np.float32)
        result = EmbeddingResult(vec, EmbeddingSource.BGE_VISUALIZED)
        normed = result.normalised()
        assert abs(np.linalg.norm(normed) - 1.0) < 1e-5

    def test_zero_vector_detection(self):
        vec = np.zeros(EMBEDDING_DIM, dtype=np.float32)
        result = EmbeddingResult(vec, EmbeddingSource.ZERO_VECTOR)
        assert result.is_zero is True

    def test_non_zero_source_not_zero(self):
        vec = np.random.rand(EMBEDDING_DIM).astype(np.float32)
        result = EmbeddingResult(vec, EmbeddingSource.BGE_VISUALIZED)
        assert result.is_zero is False

    def test_normalised_zero_vector_safe(self):
        """Zero vector normalisation should not raise."""
        vec = np.zeros(EMBEDDING_DIM, dtype=np.float32)
        result = EmbeddingResult(vec, EmbeddingSource.ZERO_VECTOR)
        normed = result.normalised()
        assert normed.shape == (EMBEDDING_DIM,)


# ── EmbeddingService — cosine similarity ──────────────────────────────────────

class TestCosineSimilarity:
    def test_identical_vectors_score_1(self):
        v = np.random.rand(EMBEDDING_DIM).astype(np.float32)
        v = v / np.linalg.norm(v)
        assert abs(EmbeddingService.cosine_similarity(v, v) - 1.0) < 1e-5

    def test_orthogonal_vectors_score_0(self):
        a = np.zeros(EMBEDDING_DIM, dtype=np.float32)
        a[0] = 1.0
        b = np.zeros(EMBEDDING_DIM, dtype=np.float32)
        b[1] = 1.0
        score = EmbeddingService.cosine_similarity(a, b)
        assert abs(score) < 1e-5

    def test_opposite_vectors_score_minus1(self):
        a = np.zeros(EMBEDDING_DIM, dtype=np.float32)
        a[0] = 1.0
        b = -a
        score = EmbeddingService.cosine_similarity(a, b)
        assert abs(score + 1.0) < 1e-5

    def test_batch_cosine_similarity_shape(self):
        query = np.random.rand(EMBEDDING_DIM).astype(np.float32)
        candidates = np.random.rand(10, EMBEDDING_DIM).astype(np.float32)
        scores = EmbeddingService.batch_cosine_similarity(query, candidates)
        assert scores.shape == (10,)

    def test_batch_similarity_correct_max(self):
        """The most similar candidate should have the highest score."""
        query = np.zeros(EMBEDDING_DIM, dtype=np.float32)
        query[0] = 1.0
        candidates = np.random.rand(5, EMBEDDING_DIM).astype(np.float32)
        # Make candidate 2 identical to query
        candidates[2] = query
        scores = EmbeddingService.batch_cosine_similarity(query, candidates)
        assert np.argmax(scores) == 2


# ── EmbeddingService — abstract query detection ───────────────────────────────

class TestAbstractQueryDetection:
    def setup_method(self):
        self.svc = EmbeddingService()

    def test_abstract_query_below_threshold(self):
        """When max similarity < threshold, query is abstract (EC-3.4)."""
        query = np.zeros(EMBEDDING_DIM, dtype=np.float32)
        query[0] = 1.0
        # Candidates are all orthogonal to query
        candidates = np.zeros((5, EMBEDDING_DIM), dtype=np.float32)
        for i in range(1, 6):
            candidates[i - 1][i] = 1.0
        assert self.svc.is_abstract_query(query, candidates) is True

    def test_non_abstract_query_above_threshold(self):
        query = np.zeros(EMBEDDING_DIM, dtype=np.float32)
        query[0] = 1.0
        candidates = np.zeros((5, EMBEDDING_DIM), dtype=np.float32)
        candidates[3] = query  # Exact match
        assert self.svc.is_abstract_query(query, candidates) is False

    def test_empty_candidates_is_abstract(self):
        query = np.random.rand(EMBEDDING_DIM).astype(np.float32)
        assert self.svc.is_abstract_query(query, np.array([])) is True


# ── EmbeddingService — near-duplicate detection ───────────────────────────────

class TestNearDuplicateDetection:
    def setup_method(self):
        self.svc = EmbeddingService()

    def test_identical_photos_clustered(self):
        """30 identical vectors should form 1 cluster (EC-3.3)."""
        base = np.random.rand(EMBEDDING_DIM).astype(np.float32)
        base = base / np.linalg.norm(base)
        vectors = np.tile(base, (30, 1))
        clusters = self.svc.find_near_duplicates(vectors, threshold=BURST_SIMILARITY_THRESHOLD)
        assert len(clusters) == 1
        assert len(clusters[0]) == 30

    def test_distinct_photos_not_clustered(self):
        """Orthogonal vectors should each be in their own cluster."""
        n = 5
        vectors = np.zeros((n, EMBEDDING_DIM), dtype=np.float32)
        for i in range(n):
            vectors[i][i] = 1.0
        clusters = self.svc.find_near_duplicates(vectors, threshold=0.9)
        assert len(clusters) == n

    def test_partial_grouping(self):
        """2 similar + 1 distinct = 2 clusters."""
        a = np.zeros(EMBEDDING_DIM, dtype=np.float32)
        a[0] = 1.0
        b = a.copy()  # Same as a — should cluster
        c = np.zeros(EMBEDDING_DIM, dtype=np.float32)
        c[1] = 1.0  # Orthogonal to a, b
        vectors = np.stack([a, b, c])
        clusters = self.svc.find_near_duplicates(vectors, threshold=0.9)
        assert len(clusters) == 2

    def test_empty_input(self):
        clusters = self.svc.find_near_duplicates(
            np.zeros((0, EMBEDDING_DIM), dtype=np.float32)
        )
        assert clusters == []


# ── embed_image with mocked HTTP ──────────────────────────────────────────────

class TestEmbedImage:
    @pytest.mark.asyncio
    async def test_returns_bge_result_on_success(self):
        svc = EmbeddingService()
        dummy_vec = np.random.rand(EMBEDDING_DIM).astype(np.float32)

        with (
            patch.object(svc, "_fetch_image", new_callable=AsyncMock) as mock_fetch,
            patch.object(svc, "_embed_image_bge") as mock_bge,
        ):
            mock_fetch.return_value = b"fake_image_bytes"
            mock_bge.return_value = dummy_vec

            result = await svc.embed_image("https://example.com/photo.jpg", "p1")
            assert result.source == EmbeddingSource.BGE_VISUALIZED
            assert result.photo_id == "p1"

    @pytest.mark.asyncio
    async def test_falls_back_to_clip_on_bge_failure(self):
        svc = EmbeddingService()
        dummy_vec = np.random.rand(EMBEDDING_DIM).astype(np.float32)

        with (
            patch.object(svc, "_fetch_image", new_callable=AsyncMock) as mock_fetch,
            patch.object(svc, "_embed_image_bge", side_effect=RuntimeError("BGE failed")),
            patch.object(svc, "_embed_image_clip") as mock_clip,
        ):
            mock_fetch.return_value = b"fake_image_bytes"
            mock_clip.return_value = dummy_vec

            result = await svc.embed_image("https://example.com/photo.jpg", "p1")
            assert result.source == EmbeddingSource.CLIP_FALLBACK

    @pytest.mark.asyncio
    async def test_returns_zero_vector_on_double_failure(self):
        svc = EmbeddingService()

        with (
            patch.object(svc, "_fetch_image", new_callable=AsyncMock) as mock_fetch,
            patch.object(svc, "_embed_image_bge", side_effect=RuntimeError("BGE failed")),
            patch.object(svc, "_embed_image_clip", side_effect=RuntimeError("CLIP failed")),
        ):
            mock_fetch.return_value = b"fake_image_bytes"
            result = await svc.embed_image("https://example.com/photo.jpg", "p1")
            assert result.source == EmbeddingSource.ZERO_VECTOR
            assert np.all(result.vector == 0)

    @pytest.mark.asyncio
    async def test_returns_zero_vector_when_fetch_fails(self):
        svc = EmbeddingService()
        with patch.object(svc, "_fetch_image", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None  # Fetch failed
            result = await svc.embed_image("https://bad-url.com/photo.jpg", "p_bad")
            assert result.source == EmbeddingSource.ZERO_VECTOR
