from pypdf import PdfReader
from pypdf.errors import PdfReadError
import logging

from backend.utils.logger import get_logger

logger = get_logger(__name__)

def extract_text(source, max_pages: int = None) -> str:
    """
    Extract text from a PDF file.
    
    Args:
        source: File-like object or path to PDF
        max_pages: Maximum number of pages to process (None for all)
    
    Returns:
        Extracted text string
    
    Raises:
        PdfReadError: If PDF is corrupted, encrypted, or unreadable
        ValueError: If source is invalid
    """
    try:
        reader = PdfReader(source)
        
        # Check if PDF is encrypted
        if reader.is_encrypted:
            raise PdfReadError("PDF is encrypted and cannot be processed")
        
        text_parts = []
        pages = reader.pages[:max_pages] if max_pages else reader.pages
        
        for page in pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        
        full_text = "\n".join(text_parts)
        logger.info(f"Extracted {len(text_parts)} pages, {len(full_text)} characters")
        
        return full_text
        
    except PdfReadError as e:
        logger.error(f"PDF read error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error extracting PDF: {e}")
        raise ValueError(f"Failed to extract text from PDF: {e}")