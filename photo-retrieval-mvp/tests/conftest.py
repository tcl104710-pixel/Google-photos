"""tests/conftest.py — shared pytest fixtures."""
import pytest

@pytest.fixture
def sample_user_id() -> str:
    return 'user_test_001'
