"""Unit tests for PDF service."""

import pytest
import tempfile
import os
from io import BytesIO
from unittest.mock import patch, MagicMock

from backend.services.pdf_service import extract_text
from pypdf import PdfWriter
from pypdf.errors import PdfReadError


class TestExtractText:
    """Test suite for extract_text function."""

    def test_extract_text_from_single_page_pdf(self):
        """Test extracting text from a single-page PDF."""
        # Create a simple PDF in memory with blank page
        pdf_buffer = BytesIO()
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        writer.write(pdf_buffer)
        pdf_buffer.seek(0)

        # This PDF has no text, so result should be empty
        text = extract_text(pdf_buffer)
        assert text == ""

    def test_extract_text_from_multi_page_pdf(self):
        """Test extracting text from multiple pages."""
        pdf_buffer = BytesIO()
        writer = PdfWriter()
        for i in range(3):
            writer.add_blank_page(width=72, height=72)
            # Note: pypdf doesn't have add_text directly, mocking instead
        pdf_buffer.seek(0)

        # Mock the PdfReader to return controlled data
        with patch("backend.services.pdf_service.PdfReader") as mock_reader:
            mock_page1 = MagicMock()
            mock_page1.extract_text.return_value = "Page 1 content"
            mock_page2 = MagicMock()
            mock_page2.extract_text.return_value = "Page 2 content"
            mock_page3 = MagicMock()
            mock_page3.extract_text.return_value = "Page 3 content"

            mock_reader.return_value.pages = [mock_page1, mock_page2, mock_page3]
            mock_reader.return_value.is_encrypted = False

            text = extract_text(pdf_buffer)
            assert "Page 1" in text
            assert "Page 2" in text
            assert "Page 3" in text

    def test_extract_text_handles_empty_pages(self):
        """Test that pages with no extractable text are handled."""
        with patch("backend.services.pdf_service.PdfReader") as mock_reader:
            mock_page = MagicMock()
            mock_page.extract_text.return_value = None
            mock_reader.return_value.pages = [mock_page]
            mock_reader.return_value.is_encrypted = False

            text = extract_text(BytesIO())
            assert text == ""

    def test_extract_text_raises_on_encrypted_pdf(self):
        """Test that encrypted PDFs raise PdfReadError."""
        with patch("backend.services.pdf_service.PdfReader") as mock_reader:
            mock_reader.return_value.is_encrypted = True

            with pytest.raises(PdfReadError, match="encrypted"):
                extract_text(BytesIO())

    def test_extract_text_raises_on_corrupted_pdf(self):
        """Test that corrupted PDFs raise appropriate exception."""
        with patch("backend.services.pdf_service.PdfReader") as mock_reader:
            mock_reader.side_effect = PdfReadError("Invalid PDF structure")

            with pytest.raises(PdfReadError):
                extract_text(BytesIO())

    def test_extract_text_with_max_pages(self):
        """Test limiting pages processed."""
        with patch("backend.services.pdf_service.PdfReader") as mock_reader:
            mock_page1 = MagicMock()
            mock_page1.extract_text.return_value = "Page 1"
            mock_page2 = MagicMock()
            mock_page2.extract_text.return_value = "Page 2"
            mock_page3 = MagicMock()
            mock_page3.extract_text.return_value = "Page 3"

            mock_reader.return_value.pages = [mock_page1, mock_page2, mock_page3]
            mock_reader.return_value.is_encrypted = False

            text = extract_text(BytesIO(), max_pages=2)
            # Should only process first 2 pages
            assert "Page 1" in text
            assert "Page 2" in text
            # Page 3 should not be in output
            assert "Page 3" not in text

    def test_extract_text_from_file_path(self, tmp_path):
        """Test extracting text from a file path."""
        # Create actual PDF file
        pdf_path = tmp_path / "test.pdf"
        writer = PdfWriter()
        # Add simple text using object-based approach
        page = writer.add_blank_page(width=72, height=72)
        # Note: pypdf text addition requires font objects, simplified test

        writer.write(str(pdf_path))

        # Mock the actual extraction for this test
        with patch("backend.services.pdf_service.PdfReader") as mock_reader:
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "File content"
            mock_reader.return_value.pages = [mock_page]
            mock_reader.return_value.is_encrypted = False

            text = extract_text(str(pdf_path))
            assert "File content" in text

    def test_extract_text_logging(self, caplog):
        """Test that extraction logs appropriately."""
        with patch("backend.services.pdf_service.PdfReader") as mock_reader:
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "Test"
            mock_reader.return_value.pages = [mock_page, mock_page]
            mock_reader.return_value.is_encrypted = False

            extract_text(BytesIO())

            # Check that info log was created
            assert any("Extracted" in record.message for record in caplog.records)
            assert any("characters" in record.message for record in caplog.records)
