"""
tests/unit/test_query_synthesis.py
"""
import numpy as np
from core.query_synthesis import QuerySynthesiser
from models.memory_context import MemoryContext, TimeRange, PersonRef, PlaceRef


class MockEmbeddingService:
    def embed_text(self, text: str) -> np.ndarray:
        return np.ones(1024, dtype=np.float32)


def test_query_synthesiser_empty():
    synth = QuerySynthesiser(MockEmbeddingService())
    ctx = MemoryContext(user_id="u1")
    
    query = synth.synthesise_query(ctx)
    
    assert query.text_embedding is None
    assert query.people_filter == []
    assert query.place_filter is None
    assert query.time_filter is None
    assert query.dimension_weights["semantic"] == 1.0


def test_query_synthesiser_strong_signals():
    synth = QuerySynthesiser(MockEmbeddingService())
    ctx = MemoryContext(user_id="u1")
    
    ctx.people.append(PersonRef(label="John"))
    ctx.confidence.people = 0.9
    
    ctx.places.append(PlaceRef(label="Goa"))
    ctx.confidence.place = 0.8
    
    query = synth.synthesise_query(ctx)
    
    # High confidence triggers hard filters
    assert query.people_filter == ["John"]
    assert query.place_filter is not None
    # Dimension weights should be populated
    assert "people" in query.dimension_weights
    assert "place" in query.dimension_weights


def test_query_synthesiser_weak_signals():
    synth = QuerySynthesiser(MockEmbeddingService())
    ctx = MemoryContext(user_id="u1")
    
    ctx.people.append(PersonRef(label="John"))
    ctx.confidence.people = 0.2  # Below 0.3 threshold
    
    query = synth.synthesise_query(ctx)
    
    # Low confidence drops hard filters
    assert query.people_filter == []
    # But it gets added to the semantic text
    assert query.text_embedding is not None
