"""
tests/unit/test_question_generator.py
"""
import pytest
from unittest.mock import AsyncMock

from llm.question_generator import QuestionGenerator
from models.memory_context import MemoryContext


@pytest.fixture
def mock_llm():
    return AsyncMock()


def test_select_best_dimension(mock_llm):
    gen = QuestionGenerator(mock_llm)
    ctx = MemoryContext(user_id="u1")
    
    # Set confidences
    ctx.confidence.people = 0.8  # > 0.7 so should be skipped
    ctx.confidence.place = 0.1   # score = (1-0.1)*0.8 = 0.72
    ctx.confidence.time = 0.5    # score = (1-0.5)*0.7 = 0.35
    ctx.confidence.activity = 0.0 # score = (1-0.0)*0.4 = 0.4
    
    best_dim = gen.select_best_dimension(ctx)
    assert best_dim == "place"


def test_select_best_dimension_all_high(mock_llm):
    gen = QuestionGenerator(mock_llm)
    ctx = MemoryContext(user_id="u1")
    
    ctx.confidence.people = 0.9
    ctx.confidence.place = 0.8
    ctx.confidence.time = 0.9
    ctx.confidence.activity = 0.9
    ctx.confidence.objects = 0.8
    ctx.confidence.appearance = 0.8
    ctx.confidence.relative_context = 0.8
    
    best_dim = gen.select_best_dimension(ctx)
    assert best_dim is None


@pytest.mark.asyncio
async def test_generate_question(mock_llm):
    mock_llm.generate_text.return_value = "Where did you go?"
    gen = QuestionGenerator(mock_llm)
    ctx = MemoryContext(user_id="u1")
    
    ctx.confidence.place = 0.0 # Will select place
    
    question = await gen.generate_question(ctx)
    
    assert question == "Where did you go?"
    assert mock_llm.generate_text.called
