"""
tests/unit/test_memory_elicitation.py
"""
import pytest
from unittest.mock import AsyncMock

from core.memory_elicitation import IntentParser, MemoryFragmentExtractor
from models.memory_context import MemoryContext


@pytest.fixture
def mock_llm():
    return AsyncMock()


@pytest.mark.asyncio
async def test_intent_parser(mock_llm):
    mock_llm.generate_json.return_value = {
        "intent": "specific_event",
        "primary_dimension": "place",
        "secondary_dimension": "activity"
    }
    
    parser = IntentParser(mock_llm)
    res = await parser.parse_intent("trip to Goa beach")
    assert res.intent == "specific_event"
    assert res.primary_dimension == "place"
    assert res.secondary_dimension == "activity"


@pytest.mark.asyncio
async def test_extractor_new_context(mock_llm):
    mock_llm.generate_json.return_value = {
        "people": [{"label": "John"}],
        "places": [{"label": "cafe"}],
        "time_expression": "last week",
        "activities": ["eating"],
        "confidence": {
            "people": 0.9,
            "place": 0.8,
            "time": 0.7,
            "activity": 0.6
        }
    }
    
    extractor = MemoryFragmentExtractor(mock_llm)
    ctx = MemoryContext(user_id="user1")
    
    new_ctx = await extractor.extract_fragments("John and I eating at cafe last week", ctx)
    
    assert len(new_ctx.people) == 1
    assert new_ctx.people[0].label == "John"
    assert new_ctx.confidence.people == 0.9
    
    assert len(new_ctx.places) == 1
    assert new_ctx.places[0].label == "cafe"
    assert new_ctx.confidence.place == 0.8
    
    assert new_ctx.time_window is not None
    assert new_ctx.time_window.raw_expression == "last week"
    
    assert new_ctx.activities == ["eating"]


@pytest.mark.asyncio
async def test_extractor_merge_context(mock_llm):
    mock_llm.generate_json.return_value = {
        "places": [{"label": "Goa"}], # new place
        "activities": ["swimming", "eating"], # existing is eating
        "confidence": {
            "place": 0.5,
            "activity": 0.9
        }
    }
    
    extractor = MemoryFragmentExtractor(mock_llm)
    ctx = MemoryContext(user_id="user1")
    ctx.activities = ["eating"]
    ctx.confidence.activity = 0.6
    
    new_ctx = await extractor.extract_fragments("also swimming in Goa", ctx)
    
    assert len(new_ctx.places) == 1
    assert new_ctx.places[0].label == "Goa"
    assert new_ctx.confidence.place == 0.5
    
    # Should merge activities and avoid dupes
    assert set(new_ctx.activities) == {"eating", "swimming"}
    # Confidence should take max
    assert new_ctx.confidence.activity == 0.9
