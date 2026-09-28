"""
tests/unit/test_memory_context.py
Unit tests for the MemoryContext, PersonRef, PlaceRef, TimeRange, and
DimensionConfidence Pydantic schemas.
"""

import pytest
from datetime import datetime, timedelta
from uuid import UUID

from models.memory_context import (
    DimensionConfidence,
    MemoryContext,
    PersonRef,
    PhotoRef,
    PlaceRef,
    TimeRange,
)


# ---------------------------------------------------------------------------
# PersonRef
# ---------------------------------------------------------------------------

class TestPersonRef:
    def test_basic_creation(self):
        p = PersonRef(label="grandma")
        assert p.label == "grandma"
        assert p.face_id is None
        assert p.resolved is False

    def test_resolved_person(self):
        p = PersonRef(label="John", face_id="face_abc123", resolved=True)
        assert p.resolved is True
        assert p.face_id == "face_abc123"

    def test_label_required(self):
        with pytest.raises(Exception):
            PersonRef()  # label is required


# ---------------------------------------------------------------------------
# PlaceRef
# ---------------------------------------------------------------------------

class TestPlaceRef:
    def test_basic_label_only(self):
        pl = PlaceRef(label="Goa")
        assert pl.label == "Goa"
        assert pl.lat_min is None

    def test_full_bbox(self):
        pl = PlaceRef(label="Goa", lat_min=14.9, lat_max=15.7, lng_min=73.6, lng_max=74.3)
        assert pl.resolved is False  # resolved is separate flag
        assert pl.lat_min == 14.9

    def test_partial_bbox_raises(self):
        """Providing only some bbox coords should raise a validation error."""
        with pytest.raises(Exception):
            PlaceRef(label="Goa", lat_min=14.9, lat_max=15.7)  # missing lng


# ---------------------------------------------------------------------------
# TimeRange
# ---------------------------------------------------------------------------

class TestTimeRange:
    def test_basic_range(self):
        start = datetime(2023, 6, 1)
        end = datetime(2023, 8, 31)
        tr = TimeRange(start=start, end=end)
        assert tr.start < tr.end

    def test_raw_expression(self):
        tr = TimeRange(raw_expression="last summer")
        assert tr.start is None
        assert tr.raw_expression == "last summer"

    def test_start_after_end_raises(self):
        with pytest.raises(Exception):
            TimeRange(
                start=datetime(2024, 1, 1),
                end=datetime(2023, 1, 1),
            )

    def test_equal_start_end_ok(self):
        now = datetime(2023, 6, 15)
        tr = TimeRange(start=now, end=now)
        assert tr.start == tr.end


# ---------------------------------------------------------------------------
# DimensionConfidence
# ---------------------------------------------------------------------------

class TestDimensionConfidence:
    def test_defaults_zero(self):
        dc = DimensionConfidence()
        assert dc.people == 0.0
        assert dc.place == 0.0
        assert dc.time == 0.0

    def test_valid_scores(self):
        dc = DimensionConfidence(people=0.9, place=0.6, time=0.3)
        assert dc.people == 0.9

    def test_out_of_range_raises(self):
        with pytest.raises(Exception):
            DimensionConfidence(people=1.5)

    def test_negative_raises(self):
        with pytest.raises(Exception):
            DimensionConfidence(activity=-0.1)


# ---------------------------------------------------------------------------
# MemoryContext
# ---------------------------------------------------------------------------

class TestMemoryContext:
    def make_context(self, user_id: str = "user_001") -> MemoryContext:
        return MemoryContext(user_id=user_id)

    def test_default_creation(self):
        ctx = self.make_context()
        assert isinstance(ctx.session_id, UUID)
        assert ctx.turn_count == 0
        assert ctx.raw_descriptions == []
        assert ctx.candidate_pool == []

    def test_add_description(self):
        ctx = self.make_context()
        ctx.add_description("Looking for my Goa trip photo")
        assert len(ctx.raw_descriptions) == 1
        assert ctx.turn_count == 1

    def test_add_multiple_descriptions(self):
        ctx = self.make_context()
        ctx.add_description("First message")
        ctx.add_description("Second message")
        assert ctx.turn_count == 2
        assert ctx.raw_descriptions[1] == "Second message"

    def test_has_minimum_signals_false_when_empty(self):
        ctx = self.make_context()
        assert ctx.has_minimum_signals() is False

    def test_has_minimum_signals_true(self):
        ctx = self.make_context()
        ctx.confidence.people = 0.9
        ctx.confidence.place = 0.7
        assert ctx.has_minimum_signals(min_dimensions=2, min_confidence=0.3) is True

    def test_has_minimum_signals_respects_threshold(self):
        ctx = self.make_context()
        ctx.confidence.people = 0.2  # Below 0.3 threshold
        ctx.confidence.place = 0.2
        assert ctx.has_minimum_signals(min_dimensions=2, min_confidence=0.3) is False

    def test_weakest_dimension_returns_lowest(self):
        ctx = self.make_context()
        ctx.confidence.people = 0.8
        ctx.confidence.place = 0.1  # lowest
        ctx.confidence.time = 0.5
        ctx.confidence.activity = 0.6
        ctx.confidence.objects = 0.4
        ctx.confidence.appearance = 0.3
        assert ctx.weakest_dimension() == "place"

    def test_json_serialisable(self):
        ctx = self.make_context()
        ctx.people = [PersonRef(label="friend")]
        ctx.time_window = TimeRange(raw_expression="last summer")
        data = ctx.model_dump()
        assert "session_id" in data
        assert data["people"][0]["label"] == "friend"

    def test_user_id_required(self):
        with pytest.raises(Exception):
            MemoryContext()  # user_id required

    def test_photo_ref_in_pool(self):
        ctx = self.make_context()
        ref = PhotoRef(photo_id="photo_001", score=0.85)
        ctx.candidate_pool.append(ref)
        assert len(ctx.candidate_pool) == 1
        assert ctx.candidate_pool[0].score == 0.85
