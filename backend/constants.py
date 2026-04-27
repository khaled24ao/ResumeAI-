"""Application-wide constants and magic values.

All hardcoded values should be defined here to ensure consistency
and ease of modification. Import these constants instead of
hardcoding values throughout the codebase.
"""

from typing import Dict, Final, List, Set

# Application metadata
APP_NAME: Final[str] = "ResumeAI"
APP_VERSION: Final[str] = "1.1.0"
APP_DESCRIPTION: Final[str] = "AI-powered resume analysis platform"

# API versioning
API_VERSION: Final[str] = "v1"
API_PREFIX: Final[str] = f"/api/{API_VERSION}"
API_V1_PREFIX: Final[str] = "/api/v1"

# HTTP status codes (for readability)
HTTP_OK: Final[int] = 200
HTTP_CREATED: Final[int] = 201
HTTP_NO_CONTENT: Final[int] = 204
HTTP_BAD_REQUEST: Final[int] = 400
HTTP_UNAUTHORIZED: Final[int] = 401
HTTP_FORBIDDEN: Final[int] = 403
HTTP_NOT_FOUND: Final[int] = 404
HTTP_METHOD_NOT_ALLOWED: Final[int] = 405
HTTP_CONFLICT: Final[int] = 409
HTTP_LENGTH_REQUIRED: Final[int] = 411
HTTP_TOO_MANY_REQUESTS: Final[int] = 429
HTTP_INTERNAL_SERVER_ERROR: Final[int] = 500
HTTP_SERVICE_UNAVAILABLE: Final[int] = 503
HTTP_UNPROCESSABLE_ENTITY: Final[int] = 422

# File upload limits
MAX_FILE_SIZE_BYTES: Final[int] = 5 * 1024 * 1024  # 5MB
MAX_FILE_SIZE_MB: Final[int] = 5
MAX_TEXT_LENGTH: Final[int] = 3000
MAX_FILENAME_LENGTH: Final[int] = 255
MAX_USER_AGENT_LENGTH: Final[int] = 255
MAX_IP_ADDRESS_LENGTH: Final[int] = 45

# Allowed file extensions
ALLOWED_EXTENSIONS: Final[Set[str]] = {".pdf"}
ALLOWED_CONTENT_TYPES: Final[Set[str]] = {"application/pdf"}

# Analysis validation bounds
SCORE_MIN: Final[int] = 1
SCORE_MAX: Final[int] = 10
MIN_STRENGTHS: Final[int] = 1
MAX_STRENGTHS: Final[int] = 10
MIN_WEAKNESSES: Final[int] = 1
MAX_WEAKNESSES: Final[int] = 10
MIN_KEYWORDS: Final[int] = 1
MAX_KEYWORDS: Final[int] = 20
SUMMARY_MIN_LENGTH: Final[int] = 10
SUMMARY_MAX_LENGTH: Final[int] = 2000

# Database
ANALYSIS_TABLE_NAME: Final[str] = "analyses"
USER_TABLE_NAME: Final[str] = "users"

# Pagination defaults
DEFAULT_PAGE_SIZE: Final[int] = 20
MAX_PAGE_SIZE: Final[int] = 100

# Rate limiting (requests per time window)
RATE_LIMIT_DEFAULT_DAY: Final[int] = 100
RATE_LIMIT_DEFAULT_HOUR: Final[int] = 20
RATE_LIMIT_DEV_HOUR: Final[int] = 1000

# AI/LLM settings
DEFAULT_AI_MODEL: Final[str] = "llama-3.1-8b-instant"
AI_TEMPERATURE: Final[float] = 0.3
AI_MAX_TOKENS: Final[int] = 2048

# Logging
LOG_FORMAT: Final[str] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL: Final[str] = "INFO"

# Prometheus metric names
METRIC_HTTP_REQUESTS_TOTAL: Final[str] = "http_requests_total"
METRIC_HTTP_REQUEST_DURATION: Final[str] = "http_request_duration_seconds"
METRIC_ANALYSES_TOTAL: Final[str] = "analyses_total"
METRIC_GROQ_CALLS_TOTAL: Final[str] = "groq_api_calls_total"
METRIC_GROQ_ERRORS_TOTAL: Final[str] = "groq_api_errors_total"
METRIC_PDF_PROCESSING: Final[str] = "pdf_processing_duration_seconds"
METRIC_DB_OPERATIONS: Final[str] = "database_operations_total"
METRIC_ACTIVE_REQUESTS: Final[str] = "active_requests"

# I18n
DEFAULT_LANGUAGE: Final[str] = "en"
SUPPORTED_LANGUAGES: Final[List[str]] = ["en", "ar"]

# Security headers
SECURITY_HEADERS: Final[Dict[str, str]] = {
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; font-src 'self'; object-src 'none'; media-src 'self'; frame-src 'none'; base-uri 'self'; form-action 'self'; report-uri ''",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "X-Permitted-Cross-Domain-Policies": "none",
}

# Error response keys
ERROR_KEY: Final[str] = "error"
DETAILS_KEY: Final[str] = "details"
RESULTS_KEY: Final[str] = "result"
ANALYSIS_ID_KEY: Final[str] = "analysis_id"
SUCCESS_KEY: Final[str] = "success"
MESSAGE_KEY: Final[str] = "message"

# PDF processing
PDF_ENCRYPTED_ERROR: Final[str] = "PDF is encrypted and cannot be processed"
PDF_CORRUPTED_ERROR: Final[str] = "Failed to read PDF - file may be corrupted"
PDF_EMPTY_ERROR: Final[str] = "PDF contains no readable text"

# AI service errors
AI_CONFIG_ERROR: Final[str] = "Service configuration error"
AI_UNAVAILABLE_ERROR: Final[str] = "Analysis failed - AI service temporarily unavailable"
AI_INVALID_RESPONSE_ERROR: Final[str] = "Invalid analysis result - AI returned malformed response"

# Database errors
DB_SAVE_ERROR: Final[str] = "Failed to save analysis to database"

# Validation messages
VALIDATION_REQUIRED_FIELD: Final[str] = "This field is required"
VALIDATION_FILE_REQUIRED: Final[str] = "No file provided"
VALIDATION_FILE_EMPTY: Final[str] = "No file selected"
VALIDATION_FILE_TYPE: Final[str] = "Only PDF files are allowed"
VALIDATION_FILE_SIZE: Final[str] = f"Maximum file size is {MAX_FILE_SIZE_MB}MB"

# Sanitization
SANITIZE_ALLOWED_TAGS: Final[Set[str]] = {"b", "i", "u", "em", "strong", "p", "br"}
SANITIZE_MAX_STRING_LENGTH: Final[int] = 10000

# Testing
TEST_GROQ_API_KEY: Final[str] = "test-groq-key"
TEST_DATABASE_URL: Final[str] = "sqlite:///:memory:"
