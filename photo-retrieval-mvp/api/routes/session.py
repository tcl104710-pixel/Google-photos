"""
api/routes/session.py
FastAPI router for managing memory elicitation and retrieval sessions.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.dependencies import (
    get_current_user_id,
    get_feedback_module,
    get_fragment_extractor,
    get_intent_parser,
    get_query_synthesiser,
    get_question_generator,
    get_ranking_engine,
    get_session_manager,
)
from core.feedback import FeedbackModule
from core.memory_elicitation import IntentParser, MemoryFragmentExtractor
from core.query_synthesis import QuerySynthesiser
from core.ranking import RankingEngine
from core.session_manager import SessionManager
from llm.question_generator import QuestionGenerator
from models.memory_context import MemoryContext
from models.photo_candidate import CandidateCluster
from models.session import SessionOutcome

router = APIRouter(prefix="/session", tags=["Session"])


class StartSessionResponse(BaseModel):
    session_id: UUID


class MessageRequest(BaseModel):
    text: str


class MessageResponse(BaseModel):
    response_text: Optional[str]
    candidates: List[CandidateCluster]
    context_snapshot: MemoryContext


class FeedbackRequest(BaseModel):
    photo_id: str
    feedback: str  # "yes", "no", "warmer"


class FeedbackResponse(BaseModel):
    candidates: List[CandidateCluster]
    context_snapshot: Optional[MemoryContext] = None


@router.post("/start", response_model=StartSessionResponse)
async def start_session(
    user_id: str = Depends(get_current_user_id),
    session_manager: SessionManager = Depends(get_session_manager),
):
    context = await session_manager.create_session(user_id)
    return StartSessionResponse(session_id=context.session_id)


@router.post("/{session_id}/message", response_model=MessageResponse)
async def handle_message(
    session_id: UUID,
    req: MessageRequest,
    user_id: str = Depends(get_current_user_id),
    session_manager: SessionManager = Depends(get_session_manager),
    intent_parser: IntentParser = Depends(get_intent_parser),
    extractor: MemoryFragmentExtractor = Depends(get_fragment_extractor),
    query_synth: QuerySynthesiser = Depends(get_query_synthesiser),
    ranker: RankingEngine = Depends(get_ranking_engine),
    q_gen: QuestionGenerator = Depends(get_question_generator),
):
    context = await session_manager.get_context(session_id)
    if not context:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    if context.user_id != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    # 1. Update context with user message
    context.add_description(req.text)
    
    # Optional: We could run IntentParser here if we needed to branch logic based on intent
    # intent_res = await intent_parser.parse_intent(req.text)
    
    # Extract fragments and merge
    context = await extractor.extract_fragments(req.text, context)
    context.turn_count += 1
    await session_manager.update_context(context)

    # 2. Synthesise Query & Rank
    query = query_synth.synthesise_query(context)
    clusters = await ranker.retrieve_and_rank(user_id, query)

    # 3. Generate clarifying question (if needed)
    response_text = None
    if not clusters or clusters[0].representative.score_total < 0.75:
        # If we don't have a strong match, try to ask a question
        response_text = await q_gen.generate_question(context)
        if not response_text and not clusters:
            response_text = "I couldn't find anything matching that description. Could you provide more details?"

    return MessageResponse(
        response_text=response_text,
        candidates=clusters,
        context_snapshot=context,
    )


@router.post("/{session_id}/feedback", response_model=FeedbackResponse)
async def handle_feedback(
    session_id: UUID,
    req: FeedbackRequest,
    user_id: str = Depends(get_current_user_id),
    session_manager: SessionManager = Depends(get_session_manager),
    feedback_mod: FeedbackModule = Depends(get_feedback_module),
    query_synth: QuerySynthesiser = Depends(get_query_synthesiser),
    ranker: RankingEngine = Depends(get_ranking_engine),
):
    context = await feedback_mod.process_feedback(session_id, req.photo_id, req.feedback)
    
    if req.feedback == "yes" or context is None:
        return FeedbackResponse(candidates=[])
        
    # Re-rank based on updated context (weights adjusted by feedback)
    query = query_synth.synthesise_query(context)
    clusters = await ranker.retrieve_and_rank(user_id, query)
    
    return FeedbackResponse(
        candidates=clusters,
        context_snapshot=context,
    )


@router.post("/{session_id}/end")
async def end_session(
    session_id: UUID,
    session_manager: SessionManager = Depends(get_session_manager),
):
    await session_manager.end_session(session_id, SessionOutcome.ABANDONED)
    return {"status": "ended"}
