"""
core/query_synthesis.py
Translates a MemoryContext into a structured RetrievalQuery.

Architecture reference: architecture.md §7.1
"""

from __future__ import annotations

import logging
from typing import Optional

from integrations.embedding_service import EmbeddingService
from models.memory_context import MemoryContext
from models.query import BoundingBox, RetrievalQuery

logger = logging.getLogger(__name__)

# Base confidence thresholds for using strict filters
STRICT_FILTER_THRESHOLD = 0.3


class QuerySynthesiser:
    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service

    def synthesise_query(self, context: MemoryContext) -> RetrievalQuery:
        """
        Translates MemoryContext to a multi-signal RetrievalQuery.
        Applies fallback strategy selectors if confidence is too low.
        """
        query = RetrievalQuery()
        
        # 1. Synthesise text embedding (fallback for all low-confidence signals)
        text_parts = []
        if context.activities:
            text_parts.append(f"Activities: {', '.join(context.activities)}")
        if context.objects:
            text_parts.append(f"Objects: {', '.join(context.objects)}")
        if context.appearance:
            text_parts.append(f"Appearance: {', '.join(context.appearance)}")
        if context.relative_context:
            text_parts.append(f"Context: {', '.join(context.relative_context)}")
        # Optionally add people/places to semantic string if they are low confidence
        if context.people and context.confidence.people < STRICT_FILTER_THRESHOLD:
            labels = [p.label for p in context.people]
            text_parts.append(f"People: {', '.join(labels)}")
        if context.places and context.confidence.place < STRICT_FILTER_THRESHOLD:
            labels = [p.label for p in context.places]
            text_parts.append(f"Place: {', '.join(labels)}")
            
        full_text = ". ".join(text_parts)
        if full_text:
            query.text_embedding = self.embedding_service.embed_text(full_text)
            
        # 2. Extract hard filters (only if confidence >= threshold)
        if context.people and context.confidence.people >= STRICT_FILTER_THRESHOLD:
            query.people_filter = [p.label for p in context.people]
            
        if context.places and context.confidence.place >= STRICT_FILTER_THRESHOLD:
            # MVP: Geocoding is mocked, so we just return a dummy bounding box if a place exists.
            # In production, this would call a geocoding API to resolve the place label to a BoundingBox.
            logger.info("Using mock bounding box for place: %s", context.places[0].label)
            query.place_filter = BoundingBox(
                min_lat=-90.0, max_lat=90.0, min_lng=-180.0, max_lng=180.0
            )
            
        if context.time_window:
            if context.confidence.time >= STRICT_FILTER_THRESHOLD:
                query.time_filter = context.time_window
            else:
                # Fallback: Widen the time filter. 
                # For MVP, we just include the original, ranking engine will handle soft scoring
                query.time_filter = context.time_window
                
        # 3. Soft labels
        if context.activities:
            query.activity_labels = context.activities
        if context.objects:
            query.object_labels = context.objects
            
        # 4. Dimension weights (used by ranking engine)
        # Normalize weights to sum to 1.0, scaled by their config priority
        raw_weights = {
            "semantic": 0.40,
            "people": 0.20 * context.confidence.people,
            "place": 0.15 * context.confidence.place,
            "time": 0.10 * context.confidence.time,
            "activity": 0.10 * context.confidence.activity,
            "appearance": 0.05 * context.confidence.appearance,
        }
        total_weight = sum(raw_weights.values())
        if total_weight > 0:
            query.dimension_weights = {k: v / total_weight for k, v in raw_weights.items()}
        else:
            query.dimension_weights = {"semantic": 1.0}
            
        return query
