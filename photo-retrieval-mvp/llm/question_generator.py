"""
llm/question_generator.py
Generates conversational clarifying questions based on the weakest memory dimension.
"""

from __future__ import annotations

import logging
from typing import Optional

from llm.groq_client import GroqClient
from models.memory_context import MemoryContext

logger = logging.getLogger(__name__)

# Discriminating power heuristics (estimated reduction in candidate pool)
DISCRIMINATING_POWER = {
    "place": 0.8,      # GPS is highly specific
    "time": 0.7,       # Time window filters significantly
    "people": 0.6,     # Face matching filters well
    "activity": 0.4,
    "objects": 0.4,
    "appearance": 0.3,
}

QUESTION_SYSTEM_PROMPT = """You are an AI assistant helping a user find a specific photo in their library.
The user's memory is vague, and you need to ask a conversational, natural, non-intrusive clarifying question.
Focus ONLY on asking about the requested dimension. Keep it to one short sentence. 
Do not be robotic or form-like. Do not list options. Do not say "Please tell me".
"""

class QuestionGenerator:
    def __init__(self, llm_client: GroqClient):
        self.llm = llm_client

    def select_best_dimension(self, context: MemoryContext) -> Optional[str]:
        """
        Selects the best dimension to ask about, based on (1 - confidence) * power.
        Skips dimensions with confidence > 0.7.
        """
        scores = {}
        confidences = {
            "people": context.confidence.people,
            "place": context.confidence.place,
            "time": context.confidence.time,
            "activity": context.confidence.activity,
            "objects": context.confidence.objects,
            "appearance": context.confidence.appearance,
        }
        
        for dim, conf in confidences.items():
            if conf > 0.7:
                continue
            # Handle dead-end heuristic: if we already asked 3 times and got nothing, maybe skip?
            # For MVP, just use the score.
            power = DISCRIMINATING_POWER.get(dim, 0.3)
            score = (1.0 - conf) * power
            scores[dim] = score
            
        if not scores:
            return None
            
        # Return dimension with highest score
        return max(scores, key=lambda k: scores[k])

    async def generate_question(self, context: MemoryContext) -> Optional[str]:
        """Generate a clarifying question based on the best missing dimension."""
        target_dim = self.select_best_dimension(context)
        if not target_dim:
            return None
            
        user_msg = (
            f"We need to ask the user about the '{target_dim}' of the photo. "
            f"Current known context: {context.model_dump_json(exclude={'raw_descriptions', 'candidate_pool', 'session_id'})}."
            "Generate one short, natural question focusing on this missing aspect."
        )
        
        question = await self.llm.generate_text(
            system_prompt=QUESTION_SYSTEM_PROMPT,
            user_message=user_msg,
            temperature=0.7,
        )
        return question
