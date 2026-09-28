"""
tests/unit/test_session.py
Unit tests for Session schemas, API request/response models,
and the SyncStatusResponse helper property.
"""

import pytest
from uuid import UUID

from models.photo_candidate import CandidateCluster, PhotoCandidate
from models.session import (
    AssistantResponse,
    EndSessionRequest,
    FeedbackRequest,
    FeedbackType,
    Session,
    SessionOutcome,
    StartSessionResponse,
    SyncStatusResponse,
    UserMessageRequest,
)


class TestSession:
    def test_default_outcome_active(self):
        s = Session(user_id="user_001")
        assert s.outcome == SessionOutcome.ACTIVE
        assert isinstance(s.session_id, UUID)

    def test_found_outcome(self):
        s = Session(user_id="user_001", outcome=SessionOutcome.FOUND, found_photo_id="photo_abc")
        assert s.found_photo_id == "photo_abc"

    def test_user_id_required(self):
        with pytest.raises(Exception):
            Session()


class TestStartSessionResponse:
    def test_defaults(self):
        r = StartSessionResponse(session_id=UUID("12345678-1234-5678-1234-567812345678"))
        assert "photo" in r.message.lower()
        assert isinstance(r.session_id, UUID)


class TestUserMessageRequest:
    def test_valid_message(self):
        req = UserMessageRequest(text="Looking for my Goa trip photo")
        assert req.text == "Looking for my Goa trip photo"

    def test_empty_message_raises(self):
        with pytest.raises(Exception):
            UserMessageRequest(text="")

    def test_message_too_long_raises(self):
        with pytest.raises(Exception):
            UserMessageRequest(text="x" * 2001)

    def test_max_length_ok(self):
        req = UserMessageRequest(text="x" * 2000)
        assert len(req.text) == 2000


class TestAssistantResponse:
    def test_defaults(self):
        r = AssistantResponse(response_text="Tell me more...")
        assert r.clusters == []
        assert r.retrieval_attempted is False
        assert r.needs_more_info is True

    def test_with_clusters(self):
        rep = PhotoCandidate(photo_id="p1", base_url="url1", score_total=0.8)
        cluster = CandidateCluster(cluster_id="c1", representative=rep)
        r = AssistantResponse(
            response_text="Here are some matches",
            clusters=[cluster],
            retrieval_attempted=True,
            needs_more_info=False,
        )
        assert len(r.clusters) == 1
        assert r.retrieval_attempted is True


class TestFeedbackRequest:
    def test_valid_yes(self):
        req = FeedbackRequest(photo_id="photo_001", feedback=FeedbackType.YES)
        assert req.feedback == FeedbackType.YES

    def test_valid_no(self):
        req = FeedbackRequest(photo_id="photo_001", feedback=FeedbackType.NO)
        assert req.feedback == "no"

    def test_valid_warmer(self):
        req = FeedbackRequest(photo_id="photo_001", feedback=FeedbackType.WARMER)
        assert req.feedback == FeedbackType.WARMER

    def test_invalid_feedback_raises(self):
        with pytest.raises(Exception):
            FeedbackRequest(photo_id="photo_001", feedback="maybe")


class TestEndSessionRequest:
    def test_found_with_photo_id(self):
        req = EndSessionRequest(outcome=SessionOutcome.FOUND, found_photo_id="photo_abc")
        assert req.found_photo_id == "photo_abc"

    def test_abandoned_no_photo(self):
        req = EndSessionRequest(outcome=SessionOutcome.ABANDONED)
        assert req.found_photo_id is None


class TestSyncStatusResponse:
    def test_progress_pct_zero_total(self):
        r = SyncStatusResponse(total_photos=0, indexed_photos=0)
        assert r.progress_pct == 0.0

    def test_progress_pct_calculation(self):
        r = SyncStatusResponse(total_photos=1000, indexed_photos=250)
        assert r.progress_pct == 25.0

    def test_progress_pct_complete(self):
        r = SyncStatusResponse(total_photos=5000, indexed_photos=5000)
        assert r.progress_pct == 100.0

    def test_index_ready_default_false(self):
        r = SyncStatusResponse(total_photos=100, indexed_photos=50)
        assert r.index_ready is False
