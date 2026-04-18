"""Unit tests for Pydantic schemas."""

import pytest
from pydantic import ValidationError

from backend.schemas.analysis import AnalysisResult, ErrorResponse


class TestAnalysisResult:
    """Test validation for AnalysisResult model."""

    def test_valid_data(self):
        """Test creation with valid data."""
        data = {
            "score": 8,
            "strengths": ["Skill 1", "Skill 2", "Skill 3"],
            "weaknesses": ["Weak 1", "Weak 2", "Weak 3"],
            "improved_summary": "A professional summary",
            "keywords_missing": ["python", "docker", "aws"],
        }
        result = AnalysisResult(**data)
        assert result.score == 8
        assert len(result.strengths) == 3

    def test_score_out_of_range_low(self):
        """Test score below 1 fails."""
        with pytest.raises(ValidationError):
            AnalysisResult(
                score=0,
                strengths=["a"],
                weaknesses=["b"],
                improved_summary="c",
                keywords_missing=["d"],
            )

    def test_score_out_of_range_high(self):
        """Test score above 10 fails."""
        with pytest.raises(ValidationError):
            AnalysisResult(
                score=11,
                strengths=["a"],
                weaknesses=["b"],
                improved_summary="c",
                keywords_missing=["d"],
            )

    def test_too_many_strengths(self):
        """Test max 10 strengths."""
        with pytest.raises(ValidationError):
            AnalysisResult(
                score=5,
                strengths=["s"] * 11,
                weaknesses=["w"],
                improved_summary="c",
                keywords_missing=["k"],
            )

    def test_too_many_weaknesses(self):
        """Test max 10 weaknesses."""
        with pytest.raises(ValidationError):
            AnalysisResult(
                score=5,
                strengths=["s"],
                weaknesses=["w"] * 11,
                improved_summary="c",
                keywords_missing=["k"],
            )

    def test_summary_too_long(self):
        """Test summary max length."""
        with pytest.raises(ValidationError):
            AnalysisResult(
                score=5,
                strengths=["s"],
                weaknesses=["w"],
                improved_summary="x" * 2001,
                keywords_missing=["k"],
            )

    def test_minimum_strengths(self):
        """Test at least 1 strength required."""
        with pytest.raises(ValidationError):
            AnalysisResult(
                score=5,
                strengths=[],
                weaknesses=["w"],
                improved_summary="c",
                keywords_missing=["k"],
            )

    def test_minimum_weaknesses(self):
        """Test at least 1 weakness required."""
        with pytest.raises(ValidationError):
            AnalysisResult(
                score=5,
                strengths=["s"],
                weaknesses=[],
                improved_summary="c",
                keywords_missing=["k"],
            )

    def test_minimum_keywords(self):
        """Test at least 1 keyword required."""
        with pytest.raises(ValidationError):
            AnalysisResult(
                score=5,
                strengths=["s"],
                weaknesses=["w"],
                improved_summary="c",
                keywords_missing=[],
            )

    def test_model_dump(self):
        """Test model_dump() returns dict."""
        result = AnalysisResult(
            score=7,
            strengths=["a"],
            weaknesses=["b"],
            improved_summary="This is a valid summary",
            keywords_missing=["d"],
        )
        data = result.model_dump()
        assert isinstance(data, dict)
        assert data["score"] == 7


class TestErrorResponse:
    """Test validation for ErrorResponse model."""

    def test_valid_error(self):
        """Test creation with error message."""
        err = ErrorResponse(error="Something went wrong")
        assert err.error == "Something went wrong"
        assert err.details is None

    def test_with_details(self):
        """Test creation with optional details."""
        err = ErrorResponse(error="Bad request", details="Invalid file type")
        assert err.error == "Bad request"
        assert err.details == "Invalid file type"

    def test_empty_error(self):
        """Test error cannot be empty string."""
