"""
tests/unit/test_vector_store.py
Unit tests for the FAISS VectorStore.
Tests index build, search, incremental update, and deletion
using a temporary directory — no GPU or large model required.
"""

from __future__ import annotations

import os
import tempfile

import numpy as np
import pytest

from integrations.vector_store import EMBEDDING_DIM, VectorStore


def random_unit_vectors(n: int, dim: int = EMBEDDING_DIM) -> np.ndarray:
    """Generate n random L2-normalised vectors."""
    vecs = np.random.rand(n, dim).astype(np.float32)
    norms = np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-10
    return vecs / norms


@pytest.fixture
def store(tmp_path):
    return VectorStore(index_dir=str(tmp_path))


@pytest.fixture
def user_id() -> str:
    return "user_test_001"


# ── build_index ────────────────────────────────────────────────────────────────

class TestBuildIndex:
    def test_builds_flat_index_small_library(self, store, user_id):
        vectors = random_unit_vectors(10)
        ids = [f"photo_{i}" for i in range(10)]
        store.build_index(user_id, vectors, ids)
        assert store.index_size(user_id) == 10

    def test_persists_to_disk(self, store, user_id, tmp_path):
        vectors = random_unit_vectors(5)
        ids = [f"p{i}" for i in range(5)]
        store.build_index(user_id, vectors, ids)
        assert (tmp_path / f"{user_id}.index").exists()
        assert (tmp_path / f"{user_id}.ids").exists()

    def test_mismatched_vectors_and_ids_raises(self, store, user_id):
        vectors = random_unit_vectors(5)
        ids = ["p1", "p2"]  # Only 2 IDs for 5 vectors
        with pytest.raises(AssertionError):
            store.build_index(user_id, vectors, ids)

    def test_wrong_dimension_raises(self, store, user_id):
        wrong_dim_vecs = np.random.rand(5, 512).astype(np.float32)
        ids = [f"p{i}" for i in range(5)]
        with pytest.raises(AssertionError):
            store.build_index(user_id, wrong_dim_vecs, ids)

    def test_rebuild_replaces_old_index(self, store, user_id):
        v1 = random_unit_vectors(3)
        store.build_index(user_id, v1, ["a", "b", "c"])
        assert store.index_size(user_id) == 3

        v2 = random_unit_vectors(7)
        store.build_index(user_id, v2, [f"p{i}" for i in range(7)])
        assert store.index_size(user_id) == 7


# ── load_index ─────────────────────────────────────────────────────────────────

class TestLoadIndex:
    def test_load_after_build(self, tmp_path, user_id):
        store1 = VectorStore(str(tmp_path))
        vectors = random_unit_vectors(5)
        store1.build_index(user_id, vectors, [f"p{i}" for i in range(5)])

        # New store instance — no in-memory cache
        store2 = VectorStore(str(tmp_path))
        success = store2.load_index(user_id)
        assert success is True
        assert store2.index_size(user_id) == 5

    def test_missing_index_returns_false(self, store, user_id):
        success = store.load_index("nonexistent_user")
        assert success is False


# ── search ─────────────────────────────────────────────────────────────────────

class TestSearch:
    def test_returns_top_k_results(self, store, user_id):
        vectors = random_unit_vectors(20)
        ids = [f"p{i}" for i in range(20)]
        store.build_index(user_id, vectors, ids)
        query = vectors[0]  # Search for the first vector itself
        results = store.search(user_id, query, top_k=5)
        assert len(results) == 5

    def test_first_result_is_most_similar(self, store, user_id):
        vectors = random_unit_vectors(10)
        ids = [f"p{i}" for i in range(10)]
        store.build_index(user_id, vectors, ids)
        query = vectors[3]  # Search for p3 exactly
        results = store.search(user_id, query, top_k=10)
        top_id, top_score = results[0]
        assert top_id == "p3"
        assert top_score > 0.99  # Near-perfect similarity

    def test_search_returns_empty_when_no_index(self, store):
        query = random_unit_vectors(1)[0]
        results = store.search("unknown_user", query, top_k=10)
        assert results == []

    def test_filter_ids_applied(self, store, user_id):
        vectors = random_unit_vectors(10)
        ids = [f"p{i}" for i in range(10)]
        store.build_index(user_id, vectors, ids)
        query = vectors[0]
        allowed = {"p0", "p1", "p2"}
        results = store.search(user_id, query, top_k=10, filter_ids=allowed)
        returned_ids = {r[0] for r in results}
        assert returned_ids.issubset(allowed)

    def test_scores_in_descending_order(self, store, user_id):
        vectors = random_unit_vectors(15)
        ids = [f"p{i}" for i in range(15)]
        store.build_index(user_id, vectors, ids)
        results = store.search(user_id, vectors[0], top_k=10)
        scores = [s for _, s in results]
        assert scores == sorted(scores, reverse=True)


# ── update_index ───────────────────────────────────────────────────────────────

class TestUpdateIndex:
    def test_incremental_adds_to_flat_index(self, store, user_id):
        initial = random_unit_vectors(5)
        store.build_index(user_id, initial, [f"p{i}" for i in range(5)])

        new_vecs = random_unit_vectors(3)
        store.update_index(user_id, new_vecs, ["p10", "p11", "p12"])
        assert store.index_size(user_id) == 8

    def test_update_on_empty_builds_fresh(self, store, user_id):
        new_vecs = random_unit_vectors(4)
        store.update_index(user_id, new_vecs, ["a", "b", "c", "d"])
        assert store.index_size(user_id) == 4


# ── delete_index ───────────────────────────────────────────────────────────────

class TestDeleteIndex:
    def test_deletes_files_and_memory(self, store, user_id, tmp_path):
        vectors = random_unit_vectors(5)
        store.build_index(user_id, vectors, [f"p{i}" for i in range(5)])
        assert store.index_loaded(user_id)

        store.delete_index(user_id)
        assert not store.index_loaded(user_id)
        assert not (tmp_path / f"{user_id}.index").exists()
        assert not (tmp_path / f"{user_id}.ids").exists()

    def test_delete_nonexistent_does_not_raise(self, store):
        # Should not raise even if index never existed
        store.delete_index("ghost_user")


# ── index_loaded / index_size ──────────────────────────────────────────────────

class TestIndexStatus:
    def test_not_loaded_by_default(self, store, user_id):
        assert not store.index_loaded(user_id)

    def test_size_zero_when_not_loaded(self, store, user_id):
        assert store.index_size(user_id) == 0
