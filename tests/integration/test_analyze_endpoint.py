"""Integration tests for analyze endpoint."""

import pytest
import json
import tempfile
import os
from io import BytesIO
from unittest.mock import patch, MagicMock

from backend.app import create_app
from backend.services.pdf_service import extract_text
from pypdf import PdfWriter


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def sample_pdf():
    """Create a sample PDF in memory."""
    pdf_buffer = BytesIO()
    writer = PdfWriter()
    # Create a simple PDF
    writer.add_blank_page(width=612, height=792)
    writer.write(pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer


class TestAnalyzeEndpoint:
    """Integration tests for /api/v1/analyze endpoint."""

    def test_analyze_success(self, client, sample_pdf):
        """Test successful analysis request."""
        # Mock AI service response
        mock_response = json.dumps({
            "score": 8,
            "strengths": ["Strong technical skills", "Good experience", "Clear structure"],
            "weaknesses": ["Missing keywords", "Too long", "No summary"],
            "improved_summary": "Improved professional summary",
            "keywords_missing": ["Python", "Docker", "AWS", "CI/CD", "Kubernetes"]
        })
        
        with patch('backend.routes.analyze.pdf_service.extract_text', return_value="Sample resume text content"):
            with patch('backend.routes.analyze.ai_service.analyze_resume', return_value=mock_response):
                response = client.post(
                    '/api/v1/analyze',
                    data={'file': (sample_pdf, 'test.pdf', 'application/pdf')},
                    content_type='multipart/form-data'
                )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert "result" in data
        result = data["result"]
        assert result["score"] == 8
        assert len(result["strengths"]) == 3
        assert len(result["weaknesses"]) == 3
        assert len(result["keywords_missing"]) == 5

    def test_analyze_no_file(self, client):
        """Test request without file."""
        response = client.post('/api/v1/analyze')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_analyze_empty_filename(self, client):
        """Test request with empty filename."""
        response = client.post(
            '/api/v1/analyze',
            data={'file': (BytesIO(b''), '', 'application/pdf')},
            content_type='multipart/form-data'
        )
        assert response.status_code == 400

    def test_analyze_invalid_extension(self, client):
        """Test request with non-PDF file."""
        response = client.post(
            '/api/v1/analyze',
            data={'file': (BytesIO(b'content'), 'test.txt', 'text/plain')},
            content_type='multipart/form-data'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "PDF" in data["error"] or "file type" in data["error"].lower()

    def test_analyze_file_too_large(self, client):
        """Test request with oversized file."""
        # Create a large buffer (6MB)
        large_data = b'x' * (6 * 1024 * 1024)
        response = client.post(
            '/api/v1/analyze',
            data={'file': (BytesIO(large_data), 'large.pdf', 'application/pdf')},
            content_type='multipart/form-data'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "large" in data.get("error", "").lower()

    def test_analyze_corrupted_pdf(self, client):
        """Test request with corrupted PDF."""
        with patch('backend.routes.analyze.pdf_service.extract_text') as mock_extract:
            mock_extract.side_effect = Exception("Corrupted PDF")
            
            response = client.post(
                '/api/v1/analyze',
                data={'file': (BytesIO(b'corrupted'), 'corrupt.pdf', 'application/pdf')},
                content_type='multipart/form-data'
            )
        
        assert response.status_code == 400

    def test_analyze_empty_pdf(self, client):
        """Test PDF with no extractable text."""
        with patch('backend.routes.analyze.pdf_service.extract_text', return_value="   "):
            response = client.post(
                '/api/v1/analyze',
                data={'file': (BytesIO(b''), 'empty.pdf', 'application/pdf')},
                content_type='multipart/form-data'
            )
        
        assert response.status_code == 400

    def test_analyze_ai_service_error(self, client, sample_pdf):
        """Test handling of AI service errors."""
        with patch('backend.routes.analyze.pdf_service.extract_text', return_value="Valid resume text content"):
            with patch('backend.routes.analyze.ai_service.analyze_resume') as mock_ai:
                mock_ai.side_effect = Exception("AI service down")
                
                response = client.post(
                    '/api/v1/analyze',
                    data={'file': (sample_pdf, 'test.pdf', 'application/pdf')},
                    content_type='multipart/form-data'
                )
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert "error" in data

    def test_analyze_invalid_ai_response(self, client, sample_pdf):
        """Test handling of malformed AI response."""
        with patch('backend.routes.analyze.pdf_service.extract_text', return_value="Valid resume text content"):
            with patch('backend.routes.analyze.ai_service.analyze_resume', return_value="Not JSON"):
                response = client.post(
                    '/api/v1/analyze',
                    data={'file': (sample_pdf, 'test.pdf', 'application/pdf')},
                    content_type='multipart/form-data'
                )
        
        assert response.status_code == 500

    def test_analyze_validation_error_in_response(self, client, sample_pdf):
        """Test handling of AI response that fails Pydantic validation."""
        # Missing required fields
        invalid_json = json.dumps({"score": 15})  # Out of range and missing fields
        with patch('backend.routes.analyze.pdf_service.extract_text', return_value="Valid resume text content"):
            with patch('backend.routes.analyze.ai_service.analyze_resume', return_value=invalid_json):
                response = client.post(
                    '/api/v1/analyze',
                    data={'file': (sample_pdf, 'test.pdf', 'application/pdf')},
                    content_type='multipart/form-data'
                )
        
        assert response.status_code == 500

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "ok"

    def test_index_returns_html(self, client):
        """Test main page returns HTML."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'ResumeAI' in response.data

    def test_text_truncation(self, client, sample_pdf):
        """Test that long text is properly truncated."""
        long_text = "x" * 5000
        
        def mock_extract(file):
            return long_text
            
        mock_valid_response = json.dumps({
            "score": 8,
            "strengths": ["Good formatting"],
            "weaknesses": ["Needs keys"],
            "improved_summary": "Truncated summary test",
            "keywords_missing": ["Git"]
        })
        
        with patch('backend.routes.analyze.pdf_service.extract_text', side_effect=mock_extract):
            with patch('backend.routes.analyze.ai_service.analyze_resume', return_value=mock_valid_response):
                response = client.post(
                    '/api/v1/analyze',
                    data={'file': (sample_pdf, 'test.pdf', 'application/pdf')},
                    content_type='multipart/form-data'
                )
        
        assert response.status_code == 200
