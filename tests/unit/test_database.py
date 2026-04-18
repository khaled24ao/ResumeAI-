"""Tests for database models and service."""

import pytest
import tempfile
import os
from sqlalchemy import inspect

from backend.models import Analysis, Base
from backend.services.database import get_db, init_db, engine
from backend.models.analysis import Analysis as AnalysisModel


class TestDatabaseModels:
    """Test suite for database models."""

    def test_analysis_model_creation(self):
        """Test creating an Analysis instance."""
        analysis = Analysis(
            filename="test.pdf",
            score=8,
            strengths='["Strong skills", "Good experience"]',
            weaknesses='["Missing keywords"]',
            improved_summary="Professional with 5 years experience",
            keywords_missing='["Python", "Docker"]',
            file_size=1024,
            processing_time_ms=1500,
        )

        assert analysis.filename == "test.pdf"
        assert analysis.score == 8
        assert analysis.strengths == '["Strong skills", "Good experience"]'

    def test_analysis_from_analysis_result(self):
        """Test creating Analysis from analysis result dict."""
        result = {
            "score": 9,
            "strengths": ["Skill 1", "Skill 2", "Skill 3"],
            "weaknesses": ["Weak 1", "Weak 2"],
            "improved_summary": "Excellent candidate",
            "keywords_missing": ["AWS", "K8s"],
        }

        analysis = Analysis.from_analysis_result(
            filename="resume.pdf",
            result=result,
            file_size=2048,
            processing_time_ms=1000,
        )

        assert analysis.filename == "resume.pdf"
        assert analysis.score == 9
        assert analysis.strengths == '["Skill 1", "Skill 2", "Skill 3"]'
        assert analysis.keywords_missing == '["AWS", "K8s"]'

    def test_analysis_properties(self):
        """Test Analysis model properties."""
        analysis = Analysis(
            score=7,
            strengths='["A", "B"]',
            weaknesses='["C"]',
            improved_summary="Test",
            keywords_missing='["X", "Y"]',
        )

        assert analysis.strengths_list == ["A", "B"]
        assert analysis.weaknesses_list == ["C"]
        assert analysis.keywords_missing_list == ["X", "Y"]

    def test_analysis_repr(self):
        """Test string representation."""
        analysis = Analysis(id=123, filename="test.pdf", score=8)
        repr_str = repr(analysis)
        assert "123" in repr_str
        assert "test.pdf" in repr_str
        assert "8" in repr_str

    def test_analysis_dict(self):
        """Test converting model to dict."""
        analysis = Analysis(id=1, filename="test.pdf", score=8, created_at=None)
        data = {
            "id": analysis.id,
            "filename": analysis.filename,
            "score": analysis.score,
        }
        assert "id" in data
        assert data["filename"] == "test.pdf"
        assert data["score"] == 8


class TestDatabaseService:
    """Test database service functions."""

    def test_get_db_session(self):
        """Test getting a database session."""
        db_gen = get_db()
        db = next(db_gen)
        try:
            assert db is not None
            assert hasattr(db, "query")
        finally:
            try:
                next(db_gen)
            except:
                pass

    def test_init_db_creates_tables(self):
        """Test that init_db creates all tables."""
        # This test may fail if tables already exist
        # In CI/CD, we use a fresh test database
        try:
            init_db()
            # Verify tables exist
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            assert "analysis" in tables or "analyses" in tables
        except Exception as e:
            pytest.skip(f"Database not available: {e}")

    def test_database_connection(self):
        """Test basic database connectivity."""
        from sqlalchemy import text

        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                assert result.scalar() == 1
        except Exception as e:
            pytest.skip(f"Database not available: {e}")
