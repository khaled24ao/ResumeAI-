"""Standardized API response wrapper.

Provides consistent response format for all API endpoints.
All responses follow the pattern:
  Success: {"success": true, "data": ...}
  Error:   {"success": false, "error": "...", "details": "..."}
"""

from typing import Any, Dict, Optional, Tuple, Union

from flask import Response, jsonify, make_response
from pydantic import BaseModel


def success_response(
    data: Any,
    status_code: int = 200,
    message: Optional[str] = None
) -> Tuple[Response, int]:
    """
    Create a successful API response.

    Args:
        data: Response payload (dict, list, or Pydantic model).
        status_code: HTTP status code.
        message: Optional success message.

    Returns:
        Tuple of (Flask Response, status_code).
    """
    payload = {"success": True}

    if message:
        payload["message"] = message

    # Handle Pydantic models
    if isinstance(data, BaseModel):
        payload["result"] = data.model_dump()
    else:
        payload["result"] = data

    return jsonify(payload), status_code


def error_response(
    error: str,
    status_code: int = 400,
    details: Optional[str] = None,
    error_code: Optional[str] = None
) -> Tuple[Response, int]:
    """
    Create an error API response.

    Args:
        error: Human-readable error message.
        status_code: HTTP status code.
        details: Optional technical details (hidden in production).
        error_code: Optional machine-readable error identifier.

    Returns:
        Tuple of (Flask Response, status_code).
    """
    payload: Dict[str, Any] = {
        "success": False,
        "error": error,
    }

    if details:
        payload["details"] = details

    if error_code:
        payload["error_code"] = error_code

    return jsonify(payload), status_code


def validation_error_response(
    errors: Dict[str, Any],
    message: str = "Validation failed"
) -> Tuple[Response, int]:
    """
    Create response for validation errors.

    Args:
        errors: Dictionary of field-to-error mappings.
        message: Summary error message.

    Returns:
        Tuple of (Flask Response, 422 status).
    """
    payload: Dict[str, Any] = {
        "success": False,
        "error": message,
        "errors": errors,
        "error_code": "VALIDATION_ERROR"
    }
    return jsonify(payload), 422


def paginated_response(
    items: list,
    total: int,
    page: int,
    per_page: int,
    extra: Optional[Dict] = None
) -> Tuple[Response, int]:
    """
    Create paginated list response.

    Args:
        items: List of items for current page.
        total: Total number of items across all pages.
        page: Current page number (1-indexed).
        per_page: Items per page.
        extra: Optional additional data to include.

    Returns:
        Tuple of (Flask Response, 200).
    """
    total_pages = (total + per_page - 1) // per_page if per_page > 0 else 0

    payload: Dict[str, Any] = {
        "success": True,
        "result": {
            "items": items,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
            }
        }
    }

    if extra:
        payload["result"].update(extra)

    return jsonify(payload), 200


def api_response(
    data: Any = None,
    error: str = None,
    **kwargs
) -> Tuple[Response, int]:
    """
    Unified response helper - automatically chooses success/error.

    Args:
        data: Data payload for success responses.
        error: Error message for error responses.
        **kwargs: Additional arguments passed to success_response or error_response.

    Returns:
        Tuple of (Flask Response, status_code).
    """
    if error:
        status = kwargs.pop("status_code", 400)
        return error_response(error, status_code=status, **kwargs)
    else:
        status = kwargs.pop("status_code", 200)
        return success_response(data if data is not None else {}, status_code=status, **kwargs)


class ResponseWrapper:
    """Helper class for building responses (alternative functional style)."""

    @staticmethod
    def ok(data: Any = None, message: str = None) -> Tuple[Response, int]:
        """Return 200 OK response."""
        return success_response(data, 200, message)

    @staticmethod
    def created(data: Any = None, message: str = "Resource created") -> Tuple[Response, int]:
        """Return 201 Created response."""
        return success_response(data, 201, message)

    @staticmethod
    def no_content() -> Tuple[Response, int]:
        """Return 204 No Content response."""
        return jsonify({}), 204

    @staticmethod
    def bad_request(error: str, details: Optional[str] = None) -> Tuple[Response, int]:
        """Return 400 Bad Request response."""
        return error_response(error, 400, details)

    @staticmethod
    def unauthorized(error: str = "Authentication required") -> Tuple[Response, int]:
        """Return 401 Unauthorized response."""
        return error_response(error, 401)

    @staticmethod
    def forbidden(error: str = "Access denied") -> Tuple[Response, int]:
        """Return 403 Forbidden response."""
        return error_response(error, 403)

    @staticmethod
    def not_found(error: str = "Resource not found") -> Tuple[Response, int]:
        """Return 404 Not Found response."""
        return error_response(error, 404)

    @staticmethod
    def conflict(error: str = "Resource conflict") -> Tuple[Response, int]:
        """Return 409 Conflict response."""
        return error_response(error, 409)

    @staticmethod
    def rate_limited(error: str = "Rate limit exceeded") -> Tuple[Response, int]:
        """Return 429 Too Many Requests response."""
        return error_response(error, 429)

    @staticmethod
    def server_error(error: str = "Internal server error") -> Tuple[Response, int]:
        """Return 500 Internal Server Error response."""
        return error_response(error, 500)

    @staticmethod
    def service_unavailable(error: str = "Service temporarily unavailable") -> Tuple[Response, int]:
        """Return 503 Service Unavailable response."""
        return error_response(error, 503)
