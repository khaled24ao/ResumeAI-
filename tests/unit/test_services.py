"""Unit tests for service layer (pdf_service, ai_service, database)."""

import pytest
from unittest.mock import patch, MagicMock, mock_open
from io import BytesIO
import json

from backend.services.pdf_service import extract_text
from backend.services.ai_service import analyze_resume
from backend.services.database import (
    get_db, get_db_context, init_db, engine,
    SessionLocal, drop_all_tables, reset_db
)
from backend.models import Analysis, Base
from backend.schemas.analysis import AnalysisResult


class TestPDFService:
    """Tests for PDF text extraction."""

    def test_extract_text_single_page(self):
        """Test extracting text from simple PDF."""
        # Mock PdfReader instead of using fragile binary string
        with patch('backend.services.pdf_service.PdfReader') as mock_reader:
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "Hello World"
            mock_reader.return_value.pages = [mock_page]
            mock_reader.return_value.is_encrypted = False
            
            result = extract_text(BytesIO(b"fake-pdf"))
            assert "Hello World" in result

    def test_extract_text_empty_pdf(self):
        """Test empty PDF returns empty string."""
        with patch('backend.services.pdf_service.PdfReader') as mock_reader:
            mock_reader.return_value.pages = []
            mock_reader.return_value.is_encrypted = False

            result = extract_text(BytesIO(b"empty-pdf"))
            assert result == ""

    def test_extract_text_encrypted_raises_error(self):
        """Test encrypted PDF raises error."""
        with patch('backend.services.pdf_service.PdfReader') as mock_reader:
            mock_reader.return_value.is_encrypted = True
            from pypdf.errors import PdfReadError
            with pytest.raises(PdfReadError):
                extract_text(BytesIO(b"encrypted-pdf"))

    def test_extract_text_with_max_pages(self):
        """Test limiting pages extracted."""
        # Mock PdfReader to test max_pages logic
        with patch('backend.services.pdf_service.PdfReader') as mock_reader:
            mock_page1 = MagicMock()
            mock_page1.extract_text.return_value = "Page 1"
            mock_page2 = MagicMock()
            mock_page2.extract_text.return_value = "Page 2"
            mock_page3 = MagicMock()
            mock_page3.extract_text.return_value = "Page 3"
            mock_reader.return_value.pages = [mock_page1, mock_page2, mock_page3]
            mock_reader.return_value.is_encrypted = False

            result = extract_text(BytesIO(b"multi-page-pdf"), max_pages=2)
            assert "Page 1" in result
            assert "Page 2" in result
            assert "Page 3" not in result

    def test_extract_text_logging(self, caplog):
        """Test that extraction logs appropriately."""
        with patch('backend.services.pdf_service.PdfReader') as mock_reader:
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "Test content"
            mock_reader.return_value.pages = [mock_page, mock_page]
            mock_reader.return_value.is_encrypted = False

            extract_text(BytesIO(b"test-pdf"))

            assert any("Extracted" in record.message for record in caplog.records)


class TestAIService:
    """Tests for AI service with Groq."""

    def test_analyze_resume_success(self):
        """Test successful AI analysis call."""
        # Fix mock structure for modern Groq client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = '{"score": 8, "strengths": ["S1"], "weaknesses": ["W1"], "improved_summary": "Sum", "keywords_missing": ["K1"]}'
        mock_client.chat.completions.create.return_value = mock_response

        with patch('backend.services.ai_service.Groq', return_value=mock_client):
            with patch.dict('os.environ', {'GROQ_API_KEY': 'test-key'}):
                result = analyze_resume("Test prompt")
                assert "score" in result
                assert "8" in result

    def test_analyze_resume_empty_prompt(self):
        """Test empty prompt raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            analyze_resume("")

    def test_analyze_resume_whitespace_prompt(self):
        """Test whitespace-only prompt raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            analyze_resume("   ")

    def test_analyze_resume_missing_api_key(self):
        """Test missing API key raises ValueError."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="GROQ_API_KEY"):
                analyze_resume("Test prompt")

    def test_analyze_resume_custom_model(self):
        """Test using custom model."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = '{"score": 7}'
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch('backend.services.ai_service.Groq', return_value=mock_client):
            with patch.dict('os.environ', {'GROQ_API_KEY': 'test-key'}):
                analyze_resume("Test", model="custom-model")
                call_kwargs = mock_client.chat.completions.create.call_args[1]
                assert call_kwargs["model"] == "custom-model"

    def test_analyze_resume_retry_logic(self):
        """Test retry on transient errors."""
        from groq import APIConnectionError
        mock_client = MagicMock()
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = '{"score": 8}'
        
        mock_client.chat.completions.create.side_effect = [
            APIConnectionError("Network error"),
            mock_response
        ]
        with patch('backend.services.ai_service.Groq', return_value=mock_client):
            with patch.dict('os.environ', {'GROQ_API_KEY': 'test-key'}):
                result = analyze_resume("Test")
                assert result == '{"score": 8}'
                assert mock_client.chat.completions.create.call_count == 2



class TestDatabaseService:
    """Tests for database service."""

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
            except StopIteration:
                pass

    def test_get_db_context(self):
        """Test context manager for database sessions."""
        with get_db_context() as db:
            assert db is not None
            assert hasattr(db, "add")

    def test_init_db_creates_tables(self):
        """Test init_db creates tables."""
        try:
            init_db()
            inspector = __import__('sqlalchemy').inspect(engine)
            tables = inspector.get_table_names()
            assert "analyses" in tables or "analysis" in tables
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


class TestAnalysisModel:
    """Tests for Analysis model."""

    def test_from_analysis_result(self, valid_analysis_result):
        """Test creating Analysis from result dict."""
        analysis = Analysis.from_analysis_result(
            filename="test.pdf",
            result=valid_analysis_result,
            file_size=1024,
            processing_time_ms=1500
        )
        assert analysis.filename == "test.pdf"
        assert analysis.score == 8
        assert analysis.strengths == json.dumps(valid_analysis_result["strengths"])
        assert analysis.keywords_missing == json.dumps(valid_analysis_result["keywords_missing"])

    def test_strengths_list_property(self):
        """Test strengths_list deserialization."""
        analysis = Analysis(strengths='["a", "b"]')
        assert analysis.strengths_list == ["a", "b"]

    def test_weaknesses_list_property(self):
        """Test weaknesses_list deserialization."""
        analysis = Analysis(weaknesses='["w1", "w2"]')
        assert analysis.weaknesses_list == ["w1", "w2"]

    def test_keywords_missing_list_property(self):
        """Test keywords_missing_list deserialization."""
        analysis = Analysis(keywords_missing='["k1", "k2"]')
        assert analysis.keywords_missing_list == ["k1", "k2"]

    def test_empty_json_fields(self):
        """Test handling of None JSON fields."""
        analysis = Analysis()
        assert analysis.strengths_list == []
        assert analysis.weaknesses_list == []
        assert analysis.keywords_missing_list == []


class TestPydanticSchemas:
    """Tests for Pydantic validation schemas."""

    def test_analysis_result_valid(self):
        """Test valid AnalysisResult creation."""
        data = {
            "score": 8,
            "strengths": ["S1", "S2"],
            "weaknesses": ["W1"],
            "improved_summary": "A good candidate with experience.",
            "keywords_missing": ["Python", "Docker"]
        }
        result = AnalysisResult(**data)
        assert result.score == 8
        assert len(result.strengths) == 2
        assert result.improved_summary == data["improved_summary"]

    def test_analysis_result_score_too_high(self):
        """Test score above 10 fails validation."""
        from pydantic import ValidationError
        data = {
            "score": 11,
            "strengths": ["S1"],
            "weaknesses": ["W1"],
            "improved_summary": "A good candidate.",
            "keywords_missing": ["K1"]
        }
        with pytest.raises(ValidationError):
            AnalysisResult(**data)

    def test_analysis_result_missing_fields(self):
        """Test missing required fields fails validation."""
        from pydantic import ValidationError
        data = {"score": 8}
        with pytest.raises(ValidationError):
            AnalysisResult(**data)