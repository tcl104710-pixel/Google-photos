"""
models/photo_candidate.py
Pydantic schema for a ranked photo candidate returned to the user.
Includes the photo's metadata, ranking signals, and explanation chips.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class ConfidenceLabel(str, Enum):
    STRONG = "Strong match"
    POSSIBLE = "Possible match"
    WEAK = "Weak match"


class MatchedDimension(BaseModel):
    """A single matched memory dimension, shown in the explanation chip."""

    dimension: str = Field(..., description="e.g. 'Place', 'Scene', 'Time'")
    value: str = Field(..., description="e.g. 'Goa', 'beach + cafe', 'evening'")


class PhotoCandidate(BaseModel):
    """
    A ranked photo candidate returned to the frontend for display.
    Contains both the photo metadata and the retrieval explanation.
    """

    # Identity
    photo_id: str = Field(..., description="Google Photos media item ID")
    cluster_id: Optional[str] = Field(
        None, description="Event cluster this photo belongs to"
    )

    # Display
    base_url: str = Field(..., description="Google Photos base URL for thumbnail display")
    filename: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    mime_type: Optional[str] = None

    # Metadata
    creation_time: Optional[datetime] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Retrieval scores (individual signals)
    score_total: float = Field(0.0, ge=0.0, le=1.0, description="Final weighted score")
    score_semantic: float = Field(0.0, ge=0.0, le=1.0)
    score_people: float = Field(0.0, ge=0.0, le=1.0)
    score_place: float = Field(0.0, ge=0.0, le=1.0)
    score_time: float = Field(0.0, ge=0.0, le=1.0)
    score_activity: float = Field(0.0, ge=0.0, le=1.0)
    score_appearance: float = Field(0.0, ge=0.0, le=1.0)

    # Explanation (shown in UI chips)
    confidence_label: ConfidenceLabel = ConfidenceLabel.WEAK
    matched_dimensions: list[MatchedDimension] = Field(default_factory=list)

    # Feedback state
    feedback: Optional[str] = Field(
        None,
        description="User feedback: 'yes' | 'no' | 'warmer' | None",
    )

    @classmethod
    def confidence_from_score(cls, score: float) -> ConfidenceLabel:
        """Map a total score to a human-readable confidence label."""
        if score >= 0.75:
            return ConfidenceLabel.STRONG
        elif score >= 0.50:
            return ConfidenceLabel.POSSIBLE
        return ConfidenceLabel.WEAK

    def explanation_text(self) -> str:
        """Format matched dimensions as a chip string, e.g. 'Goa · beach · evening'."""
        if not self.matched_dimensions:
            return "Semantic match"
        parts = [f"[{m.dimension}] {m.value}" for m in self.matched_dimensions]
        return " · ".join(parts)

    model_config = ConfigDict()

    @field_serializer("creation_time")
    def serialize_dt(self, v: datetime | None) -> str | None:
        return v.isoformat() if v else None


class CandidateCluster(BaseModel):
    """
    A cluster of near-duplicate/same-event photos.
    Only the best representative is shown by default.
    """

    cluster_id: str
    representative: PhotoCandidate
    members: list[PhotoCandidate] = Field(default_factory=list)
    event_date: Optional[datetime] = None
    event_label: Optional[str] = Field(
        None, description="e.g. 'Photos from Aug 2023 trip'"
    )

    @property
    def size(self) -> int:
        return 1 + len(self.members)
