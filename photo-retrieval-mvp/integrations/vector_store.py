"""
integrations/vector_store.py
FAISS-based per-user vector index for approximate nearest-neighbour (ANN) search.

Architecture reference: architecture.md §5.3
Edge cases handled:
  EC-3.5 (index out of sync — last_update check),
  EC-7.1 (corrupt index — rebuild from DB),
  EC-7.2 (rebuild during active session — blue-green swap),
  EC-4.4 (large library > 100k — IVFFlat index)
"""

from __future__ import annotations

import logging
import os
import tempfile
import threading
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 1024
IVF_THRESHOLD = 10_000        # Use IVFFlat above this many photos (EC-4.4)
IVF_NLIST = 100               # Number of Voronoi cells
IVF_NPROBE = 10               # Cells to search at query time (accuracy vs speed)


class VectorStore:
    """
    Per-user FAISS index. Each user gets an isolated .index file.

    Index types:
      - IndexFlatIP  — exact inner product (cosine with normalised vecs); small libraries
      - IndexIVFFlat — approximate; needed for >10k photos (EC-4.4)

    Thread safety: blue-green atomic swap on rebuild (EC-7.2).
    """

    def __init__(self, index_dir: str | Path) -> None:
        self._dir = Path(index_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        # Per-user in-memory index cache
        self._indices: dict[str, object] = {}
        # Per-user photo ID lists (position → photo_id mapping)
        self._id_maps: dict[str, list[str]] = {}
        self._lock = threading.Lock()

    # ── File paths ─────────────────────────────────────────────────────────────

    def _index_path(self, user_id: str) -> Path:
        return self._dir / f"{user_id}.index"

    def _id_map_path(self, user_id: str) -> Path:
        return self._dir / f"{user_id}.ids"

    # ── Index I/O ──────────────────────────────────────────────────────────────

    def load_index(self, user_id: str) -> bool:
        """
        Load the user's index from disk into memory.
        EC-7.1: If file is missing or corrupt, returns False (triggers rebuild).
        """
        import faiss  # type: ignore[import]

        idx_path = self._index_path(user_id)
        id_path = self._id_map_path(user_id)

        if not idx_path.exists() or not id_path.exists():
            logger.info("No index on disk for user %s", user_id)
            return False

        try:
            index = faiss.read_index(str(idx_path))
            with open(id_path) as f:
                photo_ids = [line.strip() for line in f if line.strip()]
            with self._lock:
                self._indices[user_id] = index
                self._id_maps[user_id] = photo_ids
            logger.info(
                "Loaded index for user %s: %d vectors", user_id, index.ntotal
            )
            return True
        except Exception as exc:
            logger.error("Corrupt index for user %s: %s — rebuild required", user_id, exc)
            return False

    def _save_index(self, user_id: str, index: object, photo_ids: list[str]) -> None:
        """Persist index and ID map to disk."""
        import faiss  # type: ignore[import]

        faiss.write_index(index, str(self._index_path(user_id)))  # type: ignore[arg-type]
        with open(self._id_map_path(user_id), "w") as f:
            f.write("\n".join(photo_ids))

    # ── Build / Rebuild ────────────────────────────────────────────────────────

    def build_index(
        self,
        user_id: str,
        vectors: np.ndarray,
        photo_ids: list[str],
    ) -> None:
        """
        Build (or rebuild) the FAISS index for a user.
        EC-7.2: Blue-green strategy — build to a temp file, then atomically swap.
        EC-4.4: Uses IVFFlat when library > IVF_THRESHOLD photos.
        """
        import faiss  # type: ignore[import]

        assert vectors.shape[0] == len(photo_ids), (
            f"Vector count {vectors.shape[0]} != photo_id count {len(photo_ids)}"
        )
        assert vectors.shape[1] == EMBEDDING_DIM, (
            f"Expected {EMBEDDING_DIM}-dim vectors, got {vectors.shape[1]}"
        )

        n = vectors.shape[0]
        vectors = vectors.astype(np.float32)

        # Choose index type based on library size (EC-4.4)
        if n > IVF_THRESHOLD:
            logger.info(
                "User %s has %d photos — using IVFFlat index (nlist=%d)",
                user_id, n, IVF_NLIST,
            )
            quantiser = faiss.IndexFlatIP(EMBEDDING_DIM)
            index = faiss.IndexIVFFlat(quantiser, EMBEDDING_DIM, IVF_NLIST)
            index.train(vectors)
            index.nprobe = IVF_NPROBE
        else:
            index = faiss.IndexFlatIP(EMBEDDING_DIM)

        index.add(vectors)

        # EC-7.2: Write to temp file first, then atomically rename
        with tempfile.NamedTemporaryFile(
            dir=self._dir, suffix=".index.tmp", delete=False
        ) as tmp:
            tmp_path = tmp.name

        try:
            faiss.write_index(index, tmp_path)  # type: ignore[arg-type]
            id_tmp = tmp_path + ".ids"
            with open(id_tmp, "w") as f:
                f.write("\n".join(photo_ids))

            # Atomic swap (EC-7.2)
            os.replace(tmp_path, self._index_path(user_id))
            os.replace(id_tmp, self._id_map_path(user_id))
        except Exception:
            Path(tmp_path).unlink(missing_ok=True)
            raise

        with self._lock:
            self._indices[user_id] = index
            self._id_maps[user_id] = photo_ids

        logger.info(
            "Built index for user %s: %d vectors (IndexType=%s)",
            user_id, n, "IVFFlat" if n > IVF_THRESHOLD else "FlatIP",
        )

    def update_index(
        self,
        user_id: str,
        new_vectors: np.ndarray,
        new_photo_ids: list[str],
    ) -> None:
        """
        Incremental index update: append new vectors to the existing index.
        EC-3.5: Called when last_index_update > 24h.

        Note: IVFFlat indices cannot be incrementally updated after training.
        For large libraries, triggers a full rebuild if index type changes.
        """
        import faiss  # type: ignore[import]

        if not self.load_index(user_id):
            # No existing index — build fresh
            self.build_index(user_id, new_vectors, new_photo_ids)
            return

        with self._lock:
            index = self._indices.get(user_id)
            existing_ids = self._id_maps.get(user_id, [])

        if isinstance(index, faiss.IndexFlatIP):
            # Can add directly to FlatIP
            index.add(new_vectors.astype(np.float32))  # type: ignore[union-attr]
            all_ids = existing_ids + new_photo_ids
            with self._lock:
                self._id_maps[user_id] = all_ids
            self._save_index(user_id, index, all_ids)
            logger.info(
                "Incremental update for user %s: +%d vectors", user_id, len(new_photo_ids)
            )
        else:
            # IVFFlat — must do full rebuild with all vectors
            logger.info(
                "IVFFlat index for user %s — incremental update requires full rebuild"
            )
            # Reconstruct all existing vectors (expensive but correct)
            all_vectors = np.zeros(
                (index.ntotal + len(new_photo_ids), EMBEDDING_DIM), dtype=np.float32  # type: ignore[union-attr]
            )
            index.reconstruct_n(0, index.ntotal, all_vectors[: index.ntotal])  # type: ignore[union-attr]
            all_vectors[index.ntotal :] = new_vectors.astype(np.float32)  # type: ignore[union-attr]
            all_ids = existing_ids + new_photo_ids
            self.build_index(user_id, all_vectors, all_ids)

    # ── Search ─────────────────────────────────────────────────────────────────

    def search(
        self,
        user_id: str,
        query_vector: np.ndarray,
        top_k: int = 200,
        filter_ids: Optional[set[str]] = None,
    ) -> list[tuple[str, float]]:
        """
        ANN search: returns top_k (photo_id, score) pairs.
        Optionally filter to only return photo_ids in filter_ids.

        Returns empty list if index is not loaded.
        """
        import faiss  # type: ignore[import]

        with self._lock:
            index = self._indices.get(user_id)
            photo_ids = self._id_maps.get(user_id, [])

        if index is None or index.ntotal == 0:  # type: ignore[union-attr]
            logger.warning("No index loaded for user %s", user_id)
            return []

        query = query_vector.astype(np.float32).reshape(1, -1)

        # Fetch extra candidates if filtering, to ensure top_k results after filter
        fetch_k = min(top_k * 3 if filter_ids else top_k, index.ntotal)  # type: ignore[union-attr]

        scores, indices = index.search(query, fetch_k)  # type: ignore[union-attr]
        scores = scores[0]
        indices = indices[0]

        results: list[tuple[str, float]] = []
        for idx, score in zip(indices, scores):
            if idx < 0 or idx >= len(photo_ids):
                continue
            pid = photo_ids[idx]
            if filter_ids is not None and pid not in filter_ids:
                continue
            results.append((pid, float(score)))
            if len(results) >= top_k:
                break

        return results

    def delete_index(self, user_id: str) -> None:
        """
        EC-9.2: Delete all index data for a user (called on account deletion).
        """
        with self._lock:
            self._indices.pop(user_id, None)
            self._id_maps.pop(user_id, None)

        self._index_path(user_id).unlink(missing_ok=True)
        self._id_map_path(user_id).unlink(missing_ok=True)
        logger.info("Deleted index for user %s", user_id)

    def index_size(self, user_id: str) -> int:
        """Return number of indexed vectors for a user."""
        with self._lock:
            index = self._indices.get(user_id)
        return index.ntotal if index else 0  # type: ignore[return-value,union-attr]

    def index_loaded(self, user_id: str) -> bool:
        with self._lock:
            return user_id in self._indices
