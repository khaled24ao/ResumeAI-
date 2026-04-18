"""Rate limiting configuration and middleware."""

from functools import wraps
from typing import Callable, Optional
from flask import request, jsonify, current_app, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from backend.utils.logger import get_logger

logger = get_logger(__name__)


def get_remote_address_with_fallback():
    """Get remote address with fallback for rate limiting."""
    try:
        return get_remote_address()
    except Exception:
        return "unknown"


# Initialize Flask-Limiter without binding to app yet
limiter = Limiter(
    key_func=get_remote_address_with_fallback,
    default_limits=["100 per day", "20 per hour"],
    storage_uri="memory://",  # Default to memory storage
    strategy="fixed-window",
)


def rate_limit(limit_string: Optional[str] = None):
    """
    Decorator for custom rate limits on specific endpoints.

    Args:
        limit_string: Rate limit string (e.g., "10 per minute")

    Usage:
        @app.route("/api/test")
        @rate_limit("5 per minute")
        def test():
            return "test"
    """

    def decorator(f: Callable):
        @wraps(f)
        def wrapped(*args, **kwargs):
            return f(*args, **kwargs)

        return wrapped

    return decorator


def get_rate_limit_info():
    """Get current rate limit status for the requesting IP."""
    from flask import request

    identifier = get_remote_address_with_fallback()
    try:
        limits = limiter.current_limit.get(identifier)
        return {"identifier": identifier, "limits": limits}
    except:
        return {"identifier": identifier, "limits": "Rate limiting disabled"}
