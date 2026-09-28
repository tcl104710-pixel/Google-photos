"""
tests/unit/test_ranking.py
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from core.ranking import RankingEngine
from models.query import RetrievalQuery
from models.photo_candidate import PhotoCandidate
import numpy as np
from datetime import datetime, timezone


@pytest.fixture
def mock_metadata():
    idx = AsyncMock()
    idx.query_by_person_label.return_value = ["p1", "p2"]
    return idx


@pytest.fixture
def mock_vector():
    store = MagicMock()
    # (photo_id, score)
    store.search.return_value = [("p1", 0.9), ("p2", 0.6)]
    return store


class AsyncContextManagerMock:
    def __init__(self, conn):
        self.conn = conn

    async def __aenter__(self):
        return self.conn

    async def __aexit__(self, exc_type, exc, tb):
        pass

@pytest.fixture
def mock_pool():
    from unittest.mock import MagicMock
    pool = MagicMock()
    conn = AsyncMock()
    # Mock context manager for acquire
    pool.acquire.return_value = AsyncContextManagerMock(conn)
    
    # Mock records for fetch
    conn.fetch.return_value = [
        {
            "id": "p1", "base_url": "url1", "filename": "1.jpg", 
            "width": 100, "height": 100, "mime_type": "img/jpg",
            "creation_time": datetime.now(timezone.utc),
            "latitude": 0.0, "longitude": 0.0
        },
        {
            "id": "p2", "base_url": "url2", "filename": "2.jpg", 
            "width": 100, "height": 100, "mime_type": "img/jpg",
            "creation_time": datetime.now(timezone.utc),
            "latitude": 0.0, "longitude": 0.0
        }
    ]
    return pool, conn


@pytest.mark.asyncio
async def test_ranking_engine_basic(mock_metadata, mock_vector, mock_pool):
    pool, conn = mock_pool
    engine = RankingEngine(mock_metadata, mock_vector, pool)
    
    query = RetrievalQuery(
        text_embedding=np.zeros(1024),
        people_filter=["John"],
        dimension_weights={"semantic": 0.8, "people": 0.2}
    )
    
    clusters = await engine.retrieve_and_rank("user1", query)
    
    # 2 candidates should be grouped into 1 cluster because their creation times are identical
    assert len(clusters) == 1
    
    cluster = clusters[0]
    assert cluster.size == 2
    assert cluster.representative.photo_id == "p1"
    assert cluster.representative.score_total > cluster.members[0].score_total


@pytest.mark.asyncio
async def test_ranking_engine_empty_filter(mock_metadata, mock_vector, mock_pool):
    # If the hard filter returns empty, we shouldn't return anything
    mock_metadata.query_by_person_label.return_value = []
    
    pool, conn = mock_pool
    engine = RankingEngine(mock_metadata, mock_vector, pool)
    
    query = RetrievalQuery(people_filter=["John"])
    clusters = await engine.retrieve_and_rank("user1", query)
    
    assert len(clusters) == 0
