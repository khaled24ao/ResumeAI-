"""Security middleware for Flask application.

Adds security headers and request validation to prevent common web attacks.
"""

import time

from flask import Flask, Response, g, request
from werkzeug.exceptions import RequestEntityTooLarge

from backend.config import security_config
from backend.constants import HTTP_REQUEST_ENTITY_TOO_LARGE
from backend.utils.logger import get_logger

logger = get_logger(__name__)


# Track request body sizes
_request_body_sizes: dict[str, list] = {}


def add_security_headers(response: Response) -> Response:
    """
    Add security headers to response.

    Args:
        response: Flask response object

    Returns:
        Modified response with security headers
    """
    # Content Security Policy
    csp_parts = []
    if security_config.csp_default_src:
        csp_parts.append(f"default-src {security_config.csp_default_src}")
    if security_config.csp_script_src:
        csp_parts.append(f"script-src {security_config.csp_script_src}")
    if security_config.csp_style_src:
        csp_parts.append(f"style-src {security_config.csp_style_src}")
    if security_config.csp_img_src:
        csp_parts.append(f"img-src {security_config.csp_img_src}")
    if security_config.csp_connect_src:
        csp_parts.append(f"connect-src {security_config.csp_connect_src}")
    if security_config.csp_font_src:
        csp_parts.append(f"font-src {security_config.csp_font_src}")
    if security_config.csp_object_src:
        csp_parts.append(f"object-src {security_config.csp_object_src}")
    if security_config.csp_media_src:
        csp_parts.append(f"media-src {security_config.csp_media_src}")
    if security_config.csp_frame_src:
        csp_parts.append(f"frame-src {security_config.csp_frame_src}")
    if security_config.csp_base_uri:
        csp_parts.append(f"base-uri {security_config.csp_base_uri}")
    if security_config.csp_form_action:
        csp_parts.append(f"form-action {security_config.csp_form_action}")
    if security_config.csp_report_uri:
        csp_parts.append(f"report-uri {security_config.csp_report_uri}")

    csp_value = "; ".join(csp_parts)
    response.headers["Content-Security-Policy"] = csp_value

    # HSTS (HTTP Strict Transport Security) - only over HTTPS
    if security_config.hsts_max_age > 0 and request.scheme == "https":
        hsts_value = f"max-age={security_config.hsts_max_age}"
        if security_config.hsts_include_subdomains:
            hsts_value += "; includeSubDomains"
        if security_config.hsts_preload:
            hsts_value += "; preload"
        response.headers["Strict-Transport-Security"] = hsts_value

    # X-Frame-Options
    response.headers["X-Frame-Options"] = security_config.x_frame_options

    # X-Content-Type-Options
    if security_config.content_type_nosniff:
        response.headers["X-Content-Type-Options"] = "nosniff"

    # X-XSS-Protection
    response.headers["X-XSS-Protection"] = security_config.x_xss_protection

    # Referrer-Policy
    response.headers["Referrer-Policy"] = security_config.referrer_policy

    # Permissions-Policy
    response.headers["Permissions-Policy"] = security_config.permissions_policy

    # X-Permitted-Cross-Domain-Policies
    response.headers["X-Permitted-Cross-Domain-Policies"] = (
        security_config.x_permitted_cross_domain_policies
    )

    # Remove potentially dangerous headers
    response.headers.pop("X-Powered-By", None)
    response.headers.pop("Server", None)

    return response


def validate_request_size() -> tuple[dict[str, str], int] | None:
    """
    Validate incoming request size.

    Returns:
        Error response tuple if request too large, None otherwise
    """
    content_length = request.content_length

    if content_length is not None and content_length > security_config.max_body_size:
        logger.warning(
            f"Request too large from {request.remote_addr}: {content_length} bytes"
        )
        return (
            {
                "success": False,
                "error": "Request too large",
                "details": f"Maximum request size is {security_config.max_body_size / (1024 * 1024):.1f}MB",
            },
            HTTP_REQUEST_ENTITY_TOO_LARGE,
        )

    return None


def track_request_body_size():
    """
    Track request body size for abuse detection.
    Runs before each request.
    """
    g.start_time = time.time()
    content_length = request.content_length or 0

    client_ip = request.remote_addr or "unknown"
    if client_ip not in _request_body_sizes:
        _request_body_sizes[client_ip] = []

    _request_body_sizes[client_ip].append(
        {
            "size": content_length,
            "timestamp": time.time(),
            "endpoint": request.endpoint or "unknown",
        }
    )

    # Keep only last 100 requests per IP
    if len(_request_body_sizes[client_ip]) > 100:
        _request_body_sizes[client_ip] = _request_body_sizes[client_ip][-100:]

    # Check for potential abuse
    recent_sizes = [r["size"] for r in _request_body_sizes[client_ip][-10:]]
    if len(recent_sizes) == 10 and all(
        s > security_config.max_body_size * 0.8 for s in recent_sizes
    ):
        logger.warning(
            f"Potential abuse detected from {client_ip}: consistently large requests"
        )


def security_middleware(app: Flask) -> None:
    """
    Register security middleware with Flask app.

    Adds security headers, request size validation, and tracking.

    Args:
        app: Flask application instance
    """

    @app.before_request
    def before_request_security() -> tuple[dict[str, str], int] | None:
        """Run before each request."""
        # Track request body size
        track_request_body_size()

        # Validate request size
        size_error = validate_request_size()
        if size_error:
            return size_error

        return None

    @app.after_request
    def after_request_security(response: Response) -> Response:
        """Add security headers to each response."""
        return add_security_headers(response)


def rate_limit_exceeded_handler(e: Exception) -> tuple[dict[str, str], int]:
    """
    Custom handler for rate limit exceeded errors.

    Args:
        e: Exception raised by rate limiter

    Returns:
        Error response
    """
    logger.warning(f"Rate limit exceeded: {request.remote_addr} - {request.path} - {e}")
    return (
        {
            "success": False,
            "error": "Rate limit exceeded",
            "details": "Too many requests. Please try again later.",
        },
        429,
    )


def request_entity_too_large_handler(
    e: RequestEntityTooLarge,
) -> tuple[dict[str, str], int]:
    """
    Handler for request entity too large errors.

    Args:
        e: Exception for oversized request

    Returns:
        Error response
    """
    logger.warning(
        f"Request too large from {request.remote_addr}: {request.content_length} bytes - {e}"
    )
    return (
        {
            "success": False,
            "error": "Request entity too large",
            "details": f"Maximum request size is {security_config.max_body_size / (1024 * 1024):.1f}MB",
        },
        413,
    )


def global_exception_handler(e: Exception) -> tuple[dict[str, str], int]:
    """
    Global exception handler for uncaught exceptions.

    NEVER exposes stack traces to clients.

    Args:
        e: Unhandled exception

    Returns:
        Generic error response
    """
    logger.error(f"Unhandled exception: {e}", exc_info=True)
    return (
        {
            "success": False,
            "error": "Internal server error",
            "details": "An unexpected error occurred. Please try again later.",
        },
        500,
    )
