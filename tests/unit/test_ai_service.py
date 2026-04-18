"""Unit tests for AI service."""

import pytest
from unittest.mock import patch, MagicMock, call
from groq import Groq, APIConnectionError, RateLimitError, APIError

from backend.services.ai_service import analyze_resume
from backend.utils.logger import get_logger


class TestAnalyzeResume:
    """Test suite for analyze_resume function."""

    def test_analyze_resume_success(self):
        """Test successful API call returns response."""
        mock_client = MagicMock(spec=Groq)
        mock_response = MagicMock()
        mock_response.choices[
            0
        ].message.content = '{"score": 8, "strengths": ["a"], "weaknesses": ["b"], "improved_summary": "c", "keywords_missing": ["d"]}'
        mock_client.chat.completions.create.return_value = mock_response

        with patch("backend.services.ai_service.Groq", return_value=mock_client):
            with patch.dict("os.environ", {"GROQ_API_KEY": "test-key"}):
                result = analyze_resume("Test prompt")

        assert result == mock_response.choices[0].message.content
        mock_client.chat.completions.create.assert_called_once()

    def test_analyze_resume_empty_prompt(self):
        """Test that empty prompt raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            analyze_resume("")

    def test_analyze_resume_whitespace_prompt(self):
        """Test that whitespace-only prompt raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            analyze_resume("   ")

    def test_analyze_resume_missing_api_key(self):
        """Test behavior when GROQ_API_KEY is not set."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="GROQ_API_KEY"):
                analyze_resume("Test prompt")

    def test_analyze_resume_custom_model(self):
        """Test using a custom model."""
        mock_client = MagicMock(spec=Groq)
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"score": 7}'
        mock_client.chat.completions.create.return_value = mock_response

        with patch("backend.services.ai_service.Groq", return_value=mock_client):
            with patch.dict("os.environ", {"GROQ_API_KEY": "test-key"}):
                result = analyze_resume("Test prompt", model="llama-3.3-70b-versatile")

        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == "llama-3.3-70b-versatile"

    def test_analyze_resume_with_temperature_and_tokens(self):
        """Test that temperature and max_tokens are set correctly."""
        mock_client = MagicMock(spec=Groq)
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"score": 8}'
        mock_client.chat.completions.create.return_value = mock_response

        with patch("backend.services.ai_service.Groq", return_value=mock_client):
            with patch.dict("os.environ", {"GROQ_API_KEY": "test-key"}):
                analyze_resume("Test prompt")

        _, call_kwargs = mock_client.chat.completions.create.call_args
        assert call_kwargs["temperature"] == 0.3
        assert call_kwargs["max_tokens"] == 2048

    def test_analyze_resume_logging(self, caplog):
        """Test appropriate logging occurs."""
        mock_client = MagicMock(spec=Groq)
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"score": 8}'
        mock_client.chat.completions.create.return_value = mock_response

        with patch("backend.services.ai_service.Groq", return_value=mock_client):
            with patch.dict("os.environ", {"GROQ_API_KEY": "test-key"}):
                analyze_resume("Test prompt")

        assert any("Groq API" in record.message for record in caplog.records)
        assert any(
            "Successfully received" in record.message for record in caplog.records
        )

    def test_analyze_resume_unexpected_exception(self):
        """Test handling of unexpected exceptions."""
        mock_client = MagicMock(spec=Groq)
        mock_client.chat.completions.create.side_effect = RuntimeError(
            "Unexpected error"
        )

        with patch("backend.services.ai_service.Groq", return_value=mock_client):
            with patch.dict("os.environ", {"GROQ_API_KEY": "test-key"}):
                with pytest.raises(RuntimeError):
                    analyze_resume("Test prompt")
