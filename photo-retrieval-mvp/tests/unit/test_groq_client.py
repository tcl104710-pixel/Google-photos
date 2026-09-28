"""
tests/unit/test_groq_client.py
"""
import json
from unittest.mock import AsyncMock, patch
import pytest

from llm.groq_client import GroqClient


@pytest.fixture
def groq_client():
    return GroqClient(api_key="test_key")


@pytest.mark.asyncio
async def test_generate_json_success(groq_client):
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock()]
    mock_response.choices[0].message.content = '{"intent": "test"}'
    
    with patch("groq.AsyncGroq.chat") as mock_chat:
        # Patch completions.create which is an async method
        mock_chat.completions.create = AsyncMock(return_value=mock_response)
        
        result = await groq_client.generate_json("sys", "user")
        assert result == {"intent": "test"}


@pytest.mark.asyncio
async def test_generate_json_invalid_retry(groq_client):
    mock_response_bad = AsyncMock()
    mock_response_bad.choices = [AsyncMock()]
    mock_response_bad.choices[0].message.content = 'invalid json'
    
    mock_response_good = AsyncMock()
    mock_response_good.choices = [AsyncMock()]
    mock_response_good.choices[0].message.content = '{"intent": "test"}'
    
    with patch("groq.AsyncGroq.chat") as mock_chat:
        mock_chat.completions.create = AsyncMock(side_effect=[mock_response_bad, mock_response_good])
        
        result = await groq_client.generate_json("sys", "user")
        assert result == {"intent": "test"}
        assert mock_chat.completions.create.call_count == 2


@pytest.mark.asyncio
async def test_generate_text_success(groq_client):
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock()]
    mock_response.choices[0].message.content = 'Hello world'
    
    with patch("groq.AsyncGroq.chat") as mock_chat:
        mock_chat.completions.create = AsyncMock(return_value=mock_response)
        
        result = await groq_client.generate_text("sys", "user")
        assert result == "Hello world"
