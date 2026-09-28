"""
core/ranking.py
Retrieval and multi-factor ranking engine.

Architecture reference: architecture.md §7.2, §7.3
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Optional

import asyncpg

from core.metadata_index import MetadataIndex
from integrations.vector_store import VectorStore
from models.photo_candidate import CandidateCluster, ConfidenceLabel, MatchedDimension, PhotoCandidate
from models.query import RetrievalQuery

logger = logging.getLogger(__name__)


class RankingEngine:
    def __init__(self, metadata_index: MetadataIndex, vector_store: VectorStore, pool: asyncpg.Pool):
        self.metadata = metadata_index
        self.vector_store = vector_store
        self.pool = pool

    async def retrieve_and_rank(
        self, user_id: str, query: RetrievalQuery, top_k: int = 200, output_clusters: int = 10
    ) -> list[CandidateCluster]:
        """
        Stage 1: Candidate Retrieval (Metadata Filters + ANN Search)
        Stage 2: Multi-factor Re-ranking
        Stage 3: Clustering
        """
        # --- Stage 1: Retrieval ---
        # Hard filters via Postgres
        allowed_ids: Optional[set[str]] = None
        
        # Intersection of all hard filters (if present)
        if query.people_filter:
            for person in query.people_filter:
                p_ids = await self.metadata.query_by_person_label(user_id, person)
                if allowed_ids is None:
                    allowed_ids = set(p_ids)
                else:
                    allowed_ids.intersection_update(p_ids)
                    
        if query.place_filter:
            box = query.place_filter
            p_ids = await self.metadata.query_by_gps_bbox(
                user_id, box.min_lat, box.max_lat, box.min_lng, box.max_lng
            )
            if allowed_ids is None:
                allowed_ids = set(p_ids)
            else:
                allowed_ids.intersection_update(p_ids)
                
        # Time filter requires parsing TimeRange, assume mocked for MVP or just skip DB filter 
        # and do soft scoring if it's too complex. 
        # But if allowed_ids is empty and filters were applied, we return empty.
        if allowed_ids is not None and not allowed_ids:
            return []

        # ANN Search via FAISS
        ann_results = []
        if query.text_embedding is not None:
            # Returns [(photo_id, score), ...]
            ann_results = self.vector_store.search(
                user_id, query.text_embedding, top_k=top_k, filter_ids=allowed_ids
            )
            
        candidate_ids = [pid for pid, _ in ann_results]
        if not candidate_ids and allowed_ids:
            candidate_ids = list(allowed_ids)[:top_k]
            
        if not candidate_ids:
            return []

        # Fetch photo metadata for candidates
        candidates = await self._fetch_candidates(user_id, candidate_ids)
        
        # --- Stage 2: Re-ranking ---
        # Map ANN scores
        ann_scores = {pid: score for pid, score in ann_results}
        
        for cand in candidates:
            # Base semantic score from FAISS
            cand.score_semantic = ann_scores.get(cand.photo_id, 0.0)
            
            # Boosts based on label presence (Mocked text matching for MVP)
            # In a full impl, we'd check `photo_people`, `photo_labels` tables for each candidate.
            if query.people_filter:
                cand.score_people = 1.0  # Assumes hard filter worked
                
            if query.place_filter:
                cand.score_place = 1.0
                
            # Apply weights
            w = query.dimension_weights
            cand.score_total = (
                cand.score_semantic * w.get("semantic", 1.0)
                + cand.score_people * w.get("people", 0.0)
                + cand.score_place * w.get("place", 0.0)
                + cand.score_time * w.get("time", 0.0)
                + cand.score_activity * w.get("activity", 0.0)
                + cand.score_appearance * w.get("appearance", 0.0)
            )
            cand.confidence_label = PhotoCandidate.confidence_from_score(cand.score_total)
            
            # Populate explanation chips
            if cand.score_semantic > 0.5:
                cand.matched_dimensions.append(MatchedDimension(dimension="Semantic", value="Text match"))
            if query.place_filter:
                cand.matched_dimensions.append(MatchedDimension(dimension="Place", value="Location match"))
            if query.people_filter:
                cand.matched_dimensions.append(MatchedDimension(dimension="People", value="Face match"))

        # Sort by total score descending
        candidates.sort(key=lambda x: x.score_total, reverse=True)
        
        # --- Stage 3: Clustering ---
        # Group by event (photos within 2 hours of each other).
        # For simplicity, we just take the top N since event clustering requires O(N^2) or sorting by time.
        clusters = []
        used = set()
        for cand in candidates:
            if cand.photo_id in used:
                continue
                
            cluster = CandidateCluster(
                cluster_id=f"cluster_{cand.photo_id}",
                representative=cand,
                members=[],
                event_date=cand.creation_time
            )
            used.add(cand.photo_id)
            
            # Find members (mock 2 hour window by just grouping adjacent results if they are close in time)
            for other in candidates:
                if other.photo_id not in used and cand.creation_time and other.creation_time:
                    diff = abs((cand.creation_time - other.creation_time).total_seconds())
                    if diff < 7200:  # 2 hours
                        cluster.members.append(other)
                        used.add(other.photo_id)
                        
            clusters.append(cluster)
            if len(clusters) >= output_clusters:
                break
                
        return clusters

    async def _fetch_candidates(self, user_id: str, photo_ids: list[str]) -> list[PhotoCandidate]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, base_url, filename, width, height, mime_type,
                       creation_time, latitude, longitude
                FROM photos
                WHERE user_id = $1 AND id = ANY($2)
                """,
                user_id, photo_ids
            )
            
        return [
            PhotoCandidate(
                photo_id=r["id"],
                base_url=r["base_url"],
                filename=r["filename"],
                width=r["width"],
                height=r["height"],
                mime_type=r["mime_type"],
                creation_time=r["creation_time"],
                latitude=r["latitude"],
                longitude=r["longitude"],
            )
            for r in rows
        ]
