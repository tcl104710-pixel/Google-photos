"""
models/query.py
Pydantic models representing the synthesized retrieval query.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator

from models.memory_context import TimeRange


class BoundingBox(BaseModel):
    min_lat: float
    max_lat: float
    min_lng: float
    max_lng: float


class RetrievalQuery(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    text_embedding: Optional[np.ndarray] = Field(default=None)
    people_filter: List[str] = Field(default_factory=list)
    place_filter: Optional[BoundingBox] = Field(default=None)
    time_filter: Optional[TimeRange] = Field(default=None)
    activity_labels: List[str] = Field(default_factory=list)
    object_labels: List[str] = Field(default_factory=list)
    dimension_weights: Dict[str, float] = Field(default_factory=dict)
