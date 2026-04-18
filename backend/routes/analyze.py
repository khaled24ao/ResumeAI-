import os
import json
import re
import time
from flask import Blueprint, request, jsonify
from backend.services import pdf_service, ai_service
from backend.services.database import get_db_context
from backend.schemas.analysis import AnalysisResult, ErrorResponse
from backend.models import Analysis
from backend.utils.logger import get_logger

logger = get_logger(__name__)

analyze_bp = Blueprint("analyze", __name__, url_prefix="/api/v1")

MAX_FILE_SIZE = 5 * 1024 * 1024
MAX_TEXT_LENGTH = 3000
ALLOWED_EXTENSIONS = {'.pdf'}


def allowed_file(filename: str) -> bool:
    """Check if file has an allowed extension."""
    if not filename:
        return False
    return os.path.splitext(filename.lower())[1] in ALLOWED_EXTENSIONS


def validate_and_parse_response(raw_response: str) -> dict:
    """
    Validate and parse AI response into structured format.
    
    Args:
        raw_response: Raw string response from AI
    
    Returns:
        Parsed and validated dictionary
    
    Raises:
        ValueError: If response is invalid or incomplete
    """
    json_match = re.search(r'\{[\s\S]*\}', raw_response)
    if not json_match:
        raise ValueError("No JSON found in AI response")
    
    try:
        parsed = json.loads(json_match.group())
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}")
    
    try:
        result_model = AnalysisResult(**parsed)
        return result_model.model_dump()
    except Exception as e:
        raise ValueError(f"Response validation failed: {e}")


def generate_prompt(cv_text: str) -> str:
    """Generate standardized prompt for resume analysis."""
    return f"""You are an expert HR consultant. Analyze this CV and return JSON only:

{{
  "score": 1-10,
  "strengths": [3 points],
  "weaknesses": [3 points],
  "improved_summary": "rewritten professional summary",
  "keywords_missing": [5 important keywords]
}}

CV: {cv_text}

IMPORTANT: Return ONLY valid JSON, no additional text."""


@analyze_bp.route("/analyze", methods=["POST"])
def analyze():
    """Analyze uploaded PDF resume."""
    start_time = time.time()
    logger.info("Received analysis request")
    
    try:
        # Validate file presence
        if "file" not in request.files:
            logger.warning("Request missing file")
            return jsonify(ErrorResponse(error="No file provided").model_dump()), 400
        
        file = request.files["file"]
        
        # Validate filename
        if file.filename == "":
            logger.warning("Empty filename submitted")
            return jsonify(ErrorResponse(error="No file selected").model_dump()), 400
        
        # Validate file extension
        if not allowed_file(file.filename):
            logger.warning(f"Invalid file type: {file.filename}")
            return jsonify(ErrorResponse(
                error="Invalid file type",
                details="Only PDF files are allowed"
            ).model_dump()), 400
        
        # Validate file size
        file_size = file.content_length or 0
        if file_size > MAX_FILE_SIZE:
            logger.warning(f"File too large: {file_size} bytes")
            return jsonify(ErrorResponse(
                error="File too large",
                details=f"Maximum size is {MAX_FILE_SIZE/1024/1024:.1f}MB"
            ).model_dump()), 400
        
        # Extract text from PDF
        try:
            file.seek(0)
            text = pdf_service.extract_text(file)
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            return jsonify(ErrorResponse(
                error="Failed to read PDF",
                details="File may be corrupted or encrypted"
            ).model_dump()), 400
        
        if not text.strip():
            logger.warning("PDF contains no extractable text")
            return jsonify(ErrorResponse(
                error="Empty document",
                details="PDF contains no readable text"
            ).model_dump()), 400
        
        # Truncate text
        truncated_text = text[:MAX_TEXT_LENGTH]
        if len(text) > MAX_TEXT_LENGTH:
            logger.info(f"Text truncated from {len(text)} to {MAX_TEXT_LENGTH} characters")
        
        # Generate prompt and call AI service
        prompt = generate_prompt(truncated_text)
        
        try:
            raw_result = ai_service.analyze_resume(prompt)
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            return jsonify(ErrorResponse(
                error="Service configuration error",
                details=str(e)
            ).model_dump()), 500
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return jsonify(ErrorResponse(
                error="Analysis failed",
                details="AI service temporarily unavailable"
            ).model_dump()), 500
        
        # Validate and parse response
        try:
            validated_result = validate_and_parse_response(raw_result)
        except ValueError as e:
            logger.error(f"Invalid AI response: {e}")
            return jsonify(ErrorResponse(
                error="Invalid analysis result",
                details="AI returned malformed response"
            ).model_dump()), 500
        
        # Save to database
        processing_time = int((time.time() - start_time) * 1000)
        analysis_id = None
        try:
            with get_db_context() as db:
                analysis = Analysis.from_analysis_result(
                    filename=file.filename,
                    result=validated_result,
                    file_size=file_size,
                    processing_time_ms=processing_time,
                    ip_address=request.remote_addr,
                    user_agent=request.user_agent.string[:255] if request.user_agent else None
                )
                db.add(analysis)
                db.flush()
                analysis_id = analysis.id
        except Exception as e:
            logger.error(f"Database save failed: {e}")
            # Continue without DB - graceful degradation
        
        logger.info(f"Analysis completed - score: {validated_result.get('score')}, time: {processing_time}ms")
        
        response_data = {"result": validated_result}
        if analysis_id:
            response_data["analysis_id"] = analysis_id
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.exception(f"Unexpected error in analyze endpoint: {e}")
        return jsonify(ErrorResponse(
            error="Internal server error",
            details="An unexpected error occurred"
        ).model_dump()), 500