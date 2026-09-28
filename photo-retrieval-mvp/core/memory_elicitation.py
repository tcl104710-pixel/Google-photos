"""
core/memory_elicitation.py
Intent Parser and Memory Fragment Extractor using Groq.

Architecture reference: architecture.md §6.1, §6.2
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from llm.groq_client import GroqClient
from models.memory_context import (
    DimensionConfidence,
    MemoryContext,
    PersonRef,
    PlaceRef,
    TimeRange,
)

logger = logging.getLogger(__name__)

INTENT_SYSTEM_PROMPT = """You are an AI assistant analysing a user's memory description of a photo.
Your job is to determine their intent and the primary/secondary memory dimensions they are relying on.
Valid intents: specific_event, time_period, recurring_activity, person_centric, place_centric, object_centric.
Valid dimensions: people, place, time, activity, objects, appearance, relative_context, none.

Respond ONLY with a JSON object matching this schema:
{
  "intent": "<intent_name>",
  "primary_dimension": "<dimension_name>",
  "secondary_dimension": "<dimension_name>"
}
"""

EXTRACTOR_SYSTEM_PROMPT = """You are an expert at extracting structured memory fragments from conversational photo descriptions.
Extract the entities mentioned in the user's text. Assign a confidence score from 0.0 to 1.0 for each dimension based on how specific and certain the user is. 

Dimensions:
- people: Names or relationships (e.g., "John", "my sister").
- place: Locations (e.g., "Goa", "a cafe").
- time_expression: Raw time mentions (e.g., "last summer", "2018").
- activities: Actions (e.g., "swimming", "eating").
- objects: Things (e.g., "cake", "scooter").
- appearance: Visual/mood cues (e.g., "dark", "sunset", "blurry").
- relative_context: Things that happen before/after (e.g., "after the beach").

Respond ONLY with a JSON object matching this schema:
{
  "people": [{"label": "string"}],
  "places": [{"label": "string"}],
  "time_expression": "string or null",
  "activities": ["string"],
  "objects": ["string"],
  "appearance": ["string"],
  "relative_context": ["string"],
  "confidence": {
    "people": float,
    "place": float,
    "time": float,
    "activity": float,
    "objects": float,
    "appearance": float,
    "relative_context": float
  }
}
"""

@dataclass
class IntentResult:
    intent: str
    primary_dimension: str
    secondary_dimension: str


class IntentParser:
    def __init__(self, llm_client: GroqClient):
        self.llm = llm_client

    async def parse_intent(self, user_input: str) -> IntentResult:
        """Parse user input into an intent category and primary dimensions."""
        data = await self.llm.generate_json(
            system_prompt=INTENT_SYSTEM_PROMPT,
            user_message=f"User description: {user_input}",
        )
        return IntentResult(
            intent=data.get("intent", "specific_event"),
            primary_dimension=data.get("primary_dimension", "none"),
            secondary_dimension=data.get("secondary_dimension", "none"),
        )


class MemoryFragmentExtractor:
    def __init__(self, llm_client: GroqClient):
        self.llm = llm_client

    async def extract_fragments(
        self, user_input: str, existing_context: MemoryContext
    ) -> MemoryContext:
        """
        Extract fragments from new input and merge into existing context.
        High confidence new signals overwrite lower confidence existing ones,
        otherwise they are appended/merged.
        """
        data = await self.llm.generate_json(
            system_prompt=EXTRACTOR_SYSTEM_PROMPT,
            user_message=f"User description: {user_input}",
        )
        
        # Parse output
        new_people = [PersonRef(label=p["label"]) for p in data.get("people", [])]
        new_places = [PlaceRef(label=p["label"]) for p in data.get("places", [])]
        new_time_expr = data.get("time_expression")
        new_activities = data.get("activities", [])
        new_objects = data.get("objects", [])
        new_appearance = data.get("appearance", [])
        new_relative = data.get("relative_context", [])
        
        conf = data.get("confidence", {})
        
        # Merge logic
        # For lists, we append if confidence is > 0.3. If confidence is very high (>0.8) and
        # existing is low, we might clear the old. For MVP, we append and keep the highest confidence.
        
        if new_people:
            existing_labels = {p.label.lower() for p in existing_context.people}
            for p in new_people:
                if p.label.lower() not in existing_labels:
                    existing_context.people.append(p)
            existing_context.confidence.people = max(
                existing_context.confidence.people, float(conf.get("people", 0.0))
            )

        if new_places:
            existing_locs = {p.label.lower() for p in existing_context.places}
            for p in new_places:
                if p.label.lower() not in existing_locs:
                    existing_context.places.append(p)
            existing_context.confidence.place = max(
                existing_context.confidence.place, float(conf.get("place", 0.0))
            )
            
        if new_time_expr:
            # Overwrite if we don't have one, or if new confidence is higher
            new_time_conf = float(conf.get("time", 0.0))
            if not existing_context.time_window or new_time_conf > existing_context.confidence.time:
                # Basic TimeRange creation. (Resolution to datetime happens in query synthesis or a resolver step)
                existing_context.time_window = TimeRange(raw_expression=new_time_expr)
                existing_context.confidence.time = new_time_conf
                
        # Merge string lists (set logic to avoid dupes)
        def merge_list(existing: list[str], new_items: list[str]) -> list[str]:
            res = list(existing)
            for item in new_items:
                if item.lower() not in [e.lower() for e in res]:
                    res.append(item)
            return res

        if new_activities:
            existing_context.activities = merge_list(existing_context.activities, new_activities)
            existing_context.confidence.activity = max(
                existing_context.confidence.activity, float(conf.get("activity", 0.0))
            )
            
        if new_objects:
            existing_context.objects = merge_list(existing_context.objects, new_objects)
            existing_context.confidence.objects = max(
                existing_context.confidence.objects, float(conf.get("objects", 0.0))
            )
            
        if new_appearance:
            existing_context.appearance = merge_list(existing_context.appearance, new_appearance)
            existing_context.confidence.appearance = max(
                existing_context.confidence.appearance, float(conf.get("appearance", 0.0))
            )
            
        if new_relative:
            existing_context.relative_context = merge_list(existing_context.relative_context, new_relative)
            existing_context.confidence.relative_context = max(
                existing_context.confidence.relative_context, float(conf.get("relative_context", 0.0))
            )
            
        return existing_context
