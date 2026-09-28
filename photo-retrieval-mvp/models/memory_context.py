"""
models/memory_context.py
Pydantic schema for the in-session MemoryContext object.
Represents all memory dimensions extracted from the user's conversation,
with per-dimension confidence scores and the current candidate photo pool.

Architecture reference: architecture.md §4.3
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_serializer, model_validator


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class PersonRef(BaseModel):
    """Reference to a person identified in the user's description."""

    label: str = Field(..., description="Raw label from user, e.g. 'grandma', 'John'")
    face_id: Optional[str] = Field(
        None,
        description="Google Photos face cluster ID, if resolved",
    )
    resolved: bool = Field(False, description="True if label mapped to a known face_id")


class PlaceRef(BaseModel):
    """Reference to a place extracted from the user's description."""

    label: str = Field(..., description="Raw label, e.g. 'Goa', 'a small cafe'")
    lat_min: Optional[float] = None
    lat_max: Optional[float] = None
    lng_min: Optional[float] = None
    lng_max: Optional[float] = None
    resolved: bool = Field(False, description="True if geocoded to a bounding box")

    @model_validator(mode="after")
    def bbox_all_or_none(self) -> "PlaceRef":
        coords = [self.lat_min, self.lat_max, self.lng_min, self.lng_max]
        if any(c is not None for c in coords) and not all(c is not None for c in coords):
            raise ValueError("All four bbox fields must be set together or all None")
        return self


class TimeRange(BaseModel):
    """A time window representing the user's recalled time period."""

    start: Optional[datetime] = Field(None, description="Inclusive start of window")
    end: Optional[datetime] = Field(None, description="Inclusive end of window")
    raw_expression: Optional[str] = Field(
        None,
        description="Original user phrase, e.g. 'last summer', 'around Diwali'",
    )

    @model_validator(mode="after")
    def start_before_end(self) -> "TimeRange":
        if self.start and self.end and self.start > self.end:
            raise ValueError("start must be before end")
        return self


class DimensionConfidence(BaseModel):
    """Per-dimension confidence scores in range [0.0, 1.0]."""

    people: float = Field(0.0, ge=0.0, le=1.0)
    place: float = Field(0.0, ge=0.0, le=1.0)
    time: float = Field(0.0, ge=0.0, le=1.0)
    activity: float = Field(0.0, ge=0.0, le=1.0)
    objects: float = Field(0.0, ge=0.0, le=1.0)
    appearance: float = Field(0.0, ge=0.0, le=1.0)
    relative_context: float = Field(0.0, ge=0.0, le=1.0)


class PhotoRef(BaseModel):
    """Lightweight reference to a candidate photo in the pool."""

    photo_id: str = Field(..., description="Google Photos media item ID")
    score: float = Field(0.0, ge=0.0, le=1.0, description="Current ranking score")
    cluster_id: Optional[str] = Field(None, description="Event cluster this photo belongs to")
    rejected: bool = Field(False, description="True if user explicitly rejected this photo")


# ---------------------------------------------------------------------------
# Main MemoryContext schema
# ---------------------------------------------------------------------------

class MemoryContext(BaseModel):
    """
    Stateful representation of everything the user has told the system
    during a single retrieval session.

    Updated incrementally via update_context() as the conversation progresses.
    Stored in Redis per session_id; also checkpointed to PostgreSQL.
    """

    session_id: UUID = Field(default_factory=uuid4)
    user_id: str = Field(..., description="Authenticated user identifier")

    # Raw conversation history
    raw_descriptions: list[str] = Field(
        default_factory=list,
        description="Ordered list of all user inputs in this session",
    )

    # Memory dimensions (all optional — filled as conversation progresses)
    people: list[PersonRef] = Field(default_factory=list)
    places: list[PlaceRef] = Field(default_factory=list)
    time_window: Optional[TimeRange] = None
    activities: list[str] = Field(
        default_factory=list,
        description="Activity labels, e.g. ['eating', 'beach', 'swimming']",
    )
    objects: list[str] = Field(
        default_factory=list,
        description="Object labels, e.g. ['scooter', 'sunset', 'birthday cake']",
    )
    appearance: list[str] = Field(
        default_factory=list,
        description="Appearance cues, e.g. ['golden hour', 'crowded', 'indoor']",
    )
    relative_context: list[str] = Field(
        default_factory=list,
        description="Relative context cues, e.g. ['after the market visit']",
    )

    # Confidence scores per dimension
    confidence: DimensionConfidence = Field(default_factory=DimensionConfidence)

    # Current candidate photo pool
    candidate_pool: list[PhotoRef] = Field(default_factory=list)

    # Session metadata
    turn_count: int = Field(0, ge=0, description="Number of conversational turns so far")
    intent: Optional[str] = Field(
        None,
        description="Detected intent: specific_event | time_period | recurring_activity | "
                    "person_centric | place_centric | object_centric",
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict()

    @field_serializer("created_at", "updated_at")
    def serialize_dt(self, v: datetime) -> str:
        return v.isoformat()

    @field_serializer("session_id")
    def serialize_uuid(self, v: UUID) -> str:
        return str(v)

    def add_description(self, text: str) -> None:
        """Append a new user message to the raw description history."""
        self.raw_descriptions.append(text)
        self.turn_count += 1
        self.updated_at = datetime.now(timezone.utc)

    def has_minimum_signals(self, min_dimensions: int = 2, min_confidence: float = 0.3) -> bool:
        """Return True if enough confident dimensions exist to attempt retrieval."""
        confident = sum(
            1
            for v in [
                self.confidence.people,
                self.confidence.place,
                self.confidence.time,
                self.confidence.activity,
                self.confidence.objects,
                self.confidence.appearance,
            ]
            if v >= min_confidence
        )
        return confident >= min_dimensions

    def weakest_dimension(self) -> str:
        """Return the name of the least confident dimension (for clarifying questions)."""
        scores = {
            "people": self.confidence.people,
            "place": self.confidence.place,
            "time": self.confidence.time,
            "activity": self.confidence.activity,
            "objects": self.confidence.objects,
            "appearance": self.confidence.appearance,
        }
        return min(scores, key=lambda k: scores[k])
