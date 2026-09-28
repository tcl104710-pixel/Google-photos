"""
tests/unit/test_photo_candidate.py
Unit tests for PhotoCandidate, CandidateCluster, and ConfidenceLabel schemas.
"""

import pytest
from datetime import datetime

from models.photo_candidate import (
    CandidateCluster,
    ConfidenceLabel,
    MatchedDimension,
    PhotoCandidate,
)


def make_candidate(
    photo_id: str = "photo_001",
    score_total: float = 0.8,
    base_url: str = "https://photos.google.com/id/photo_001",
) -> PhotoCandidate:
    return PhotoCandidate(photo_id=photo_id, score_total=score_total, base_url=base_url)


class TestConfidenceLabel:
    def test_strong_above_75(self):
        assert PhotoCandidate.confidence_from_score(0.75) == ConfidenceLabel.STRONG
        assert PhotoCandidate.confidence_from_score(0.99) == ConfidenceLabel.STRONG

    def test_possible_50_to_74(self):
        assert PhotoCandidate.confidence_from_score(0.50) == ConfidenceLabel.POSSIBLE
        assert PhotoCandidate.confidence_from_score(0.74) == ConfidenceLabel.POSSIBLE

    def test_weak_below_50(self):
        assert PhotoCandidate.confidence_from_score(0.49) == ConfidenceLabel.WEAK
        assert PhotoCandidate.confidence_from_score(0.0) == ConfidenceLabel.WEAK


class TestPhotoCandidate:
    def test_basic_creation(self):
        c = make_candidate()
        assert c.photo_id == "photo_001"
        assert c.score_total == 0.8

    def test_score_out_of_range(self):
        with pytest.raises(Exception):
            PhotoCandidate(photo_id="x", base_url="url", score_total=1.5)

    def test_explanation_text_with_dimensions(self):
        c = make_candidate()
        c.matched_dimensions = [
            MatchedDimension(dimension="Place", value="Goa"),
            MatchedDimension(dimension="Scene", value="beach"),
        ]
        text = c.explanation_text()
        assert "Goa" in text
        assert "beach" in text
        assert "·" in text

    def test_explanation_text_no_dimensions(self):
        c = make_candidate()
        assert c.explanation_text() == "Semantic match"

    def test_feedback_default_none(self):
        c = make_candidate()
        assert c.feedback is None

    def test_creation_time_optional(self):
        c = make_candidate()
        assert c.creation_time is None

    def test_json_serialisable(self):
        c = make_candidate()
        c.creation_time = datetime(2023, 8, 15, 10, 30)
        data = c.model_dump()
        assert data["photo_id"] == "photo_001"


class TestCandidateCluster:
    def test_size_representative_only(self):
        rep = make_candidate()
        cluster = CandidateCluster(cluster_id="cl_001", representative=rep)
        assert cluster.size == 1

    def test_size_with_members(self):
        rep = make_candidate("photo_001")
        m1 = make_candidate("photo_002")
        m2 = make_candidate("photo_003")
        cluster = CandidateCluster(
            cluster_id="cl_001",
            representative=rep,
            members=[m1, m2],
        )
        assert cluster.size == 3

    def test_event_label(self):
        rep = make_candidate()
        cluster = CandidateCluster(
            cluster_id="cl_001",
            representative=rep,
            event_label="Photos from Aug 2023 trip",
        )
        assert "Aug 2023" in cluster.event_label
