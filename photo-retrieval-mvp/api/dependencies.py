"""
api/dependencies.py
FastAPI dependency injection for services and database connections.
"""

from __future__ import annotations

import os
from typing import AsyncGenerator

import asyncpg
from redis.asyncio import Redis

from core.feedback import FeedbackModule
from core.memory_elicitation import IntentParser, MemoryFragmentExtractor
from core.metadata_index import MetadataIndex
from core.query_synthesis import QuerySynthesiser
from core.ranking import RankingEngine
from core.session_manager import SessionManager
from integrations.embedding_service import EmbeddingService
from integrations.google_photos import GooglePhotosAdapter
from integrations.vector_store import VectorStore
from llm.groq_client import GroqClient
from llm.question_generator import QuestionGenerator

# Global pools (initialized in main app lifespan)
_pg_pool: asyncpg.Pool | None = None
_redis_client: Redis | None = None

# Global services
_embedding_service: EmbeddingService | None = None
_vector_store: VectorStore | None = None
_google_photos: GooglePhotosAdapter | None = None
_metadata_index: MetadataIndex | None = None
_groq_client: GroqClient | None = None
_session_manager: SessionManager | None = None
_ranking_engine: RankingEngine | None = None
_query_synthesiser: QuerySynthesiser | None = None
_intent_parser: IntentParser | None = None
_fragment_extractor: MemoryFragmentExtractor | None = None
_question_generator: QuestionGenerator | None = None
_feedback_module: FeedbackModule | None = None


def get_pg_pool() -> asyncpg.Pool:
    if _pg_pool is None:
        raise RuntimeError("Postgres pool not initialized")
    return _pg_pool


def get_redis() -> Redis:
    if _redis_client is None:
        raise RuntimeError("Redis not initialized")
    return _redis_client


def get_metadata_index() -> MetadataIndex:
    if _metadata_index is None:
        raise RuntimeError("MetadataIndex not initialized")
    return _metadata_index


def get_google_photos() -> GooglePhotosAdapter:
    if _google_photos is None:
        raise RuntimeError("GooglePhotosAdapter not initialized")
    return _google_photos


def get_session_manager() -> SessionManager:
    if _session_manager is None:
        raise RuntimeError("SessionManager not initialized")
    return _session_manager


def get_intent_parser() -> IntentParser:
    if _intent_parser is None:
        raise RuntimeError("IntentParser not initialized")
    return _intent_parser


def get_fragment_extractor() -> MemoryFragmentExtractor:
    if _fragment_extractor is None:
        raise RuntimeError("MemoryFragmentExtractor not initialized")
    return _fragment_extractor


def get_question_generator() -> QuestionGenerator:
    if _question_generator is None:
        raise RuntimeError("QuestionGenerator not initialized")
    return _question_generator


def get_query_synthesiser() -> QuerySynthesiser:
    if _query_synthesiser is None:
        raise RuntimeError("QuerySynthesiser not initialized")
    return _query_synthesiser


def get_ranking_engine() -> RankingEngine:
    if _ranking_engine is None:
        raise RuntimeError("RankingEngine not initialized")
    return _ranking_engine


def get_feedback_module() -> FeedbackModule:
    if _feedback_module is None:
        raise RuntimeError("FeedbackModule not initialized")
    return _feedback_module


# Mock dependency for getting the current user ID
def get_current_user_id() -> str:
    # In a real app, this would extract the user ID from an auth cookie/token
    return "test_user_001"
