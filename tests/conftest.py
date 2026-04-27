"""Pytest configuration and fixtures."""

import sys
import os
import pytest

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# Test environment variables
os.environ.setdefault("GROQ_API_KEY", "test-key-not-real")
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["REDIS_URL"] = ""  # Force in-memory limiter

@pytest.fixture
def mock_groq_response():
    """Fixture to create a mock Groq API response."""
    def _create_response(content=None):
        if content is None:
            content = '{"score": 8, "strengths": ["S1", "S2"], "weaknesses": ["W1"], "improved_summary": "Summary", "keywords_missing": ["K1"]}'
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = content
        return mock_response
    return _create_response

@pytest.fixture
def valid_analysis_result():
    """Fixture for a valid analysis result dictionary."""
    return {
        "score": 8,
        "strengths": ["Strong technical background", "Clear communication"],
        "weaknesses": ["Lack of leadership experience"],
        "improved_summary": "Experienced software engineer with a focus on Python and distributed systems.",
        "keywords_missing": ["Kubernetes", "GraphQL"]
    }

from unittest.mock import MagicMock