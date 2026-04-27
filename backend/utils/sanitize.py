"""Input sanitization and validation utilities.

Provides safe input cleaning and validation to prevent injection attacks
and ensure data integrity.
"""

import html
import re
from typing import Any
import unicodedata

from backend.constants import (
    MAX_FILENAME_LENGTH,
    MAX_IP_ADDRESS_LENGTH,
    MAX_USER_AGENT_LENGTH,
    SANITIZE_MAX_STRING_LENGTH,
)


def sanitize_filename(filename: str | None) -> str:
    """
    Sanitize filename to prevent path traversal and other attacks.

    Removes dangerous characters and normalizes the filename.
    Only keeps alphanumeric, underscore, hyphen, dot, and space.

    Args:
        filename: Raw filename from user input

    Returns:
        Sanitized safe filename
    """
    if not filename:
        return "unknown"

    # Strip path components
    filename = filename.strip()
    filename = filename.split("/")[-1].split("\\")[-1]

    # Normalize unicode
    filename = unicodedata.normalize("NFKD", filename)

    # Remove or replace dangerous characters
    # Keep: alphanumeric, underscore, hyphen, dot, space
    filename = re.sub(r"[^a-zA-Z0-9_\-\.\s]", "", filename)

    # Collapse multiple spaces/dots/hyphens
    filename = re.sub(r"\s+", " ", filename)
    filename = re.sub(r"\.+", ".", filename)
    filename = re.sub(r"\-+", "-", filename)

    # Strip leading/trailing whitespace and dots
    filename = filename.strip(" .")

    # Truncate to safe length
    if len(filename) > MAX_FILENAME_LENGTH:
        name, ext = "", ""
        if "." in filename:
            parts = filename.rsplit(".", 1)
            name = parts[0][: MAX_FILENAME_LENGTH - 10]
            ext = "." + parts[1][:9]
        else:
            name = filename[:MAX_FILENAME_LENGTH]
        filename = name + ext

    return filename if filename else "file"


def sanitize_string(
    value: str | None, max_length: int = SANITIZE_MAX_STRING_LENGTH
) -> str:
    """
    Sanitize free-form string input.

    Args:
        value: Input string to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string
    """
    if not value:
        return ""

    # Convert to string and strip
    value = str(value).strip()

    # Remove null bytes and other control characters except newlines/tabs
    value = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", value)

    # Truncate to max length
    if len(value) > max_length:
        value = value[:max_length]

    return value


def sanitize_user_agent(user_agent: str | None) -> str:
    """
    Sanitize User-Agent string.

    Args:
        user_agent: Raw User-Agent from request

    Returns:
        Sanitized User-Agent
    """
    if not user_agent:
        return ""

    value = str(user_agent).strip()

    # Remove null bytes
    value = re.sub(r"[\x00-\x1F\x7F]", "", value)

    # Truncate to safe length
    if len(value) > MAX_USER_AGENT_LENGTH:
        value = value[:MAX_USER_AGENT_LENGTH]

    return value


def sanitize_ip_address(ip_address: str | None) -> str:
    """
    Sanitize IP address.

    Basic validation to prevent header injection.

    Args:
        ip_address: Raw IP address from request

    Returns:
        Sanitized IP address
    """
    if not ip_address:
        return ""

    value = str(ip_address).strip()

    # Remove null bytes and dangerous characters
    value = re.sub(r"[\x00-\x1F\x7F]", "", value)

    # Basic IP pattern (IPv4 and IPv6)
    ip_pattern = r"^[0-9a-fA-F:.]+$"
    if not re.match(ip_pattern, value):
        return ""

    # Truncate to safe length
    if len(value) > MAX_IP_ADDRESS_LENGTH:
        value = value[:MAX_IP_ADDRESS_LENGTH]

    return value


def sanitize_text_for_display(text: str | None) -> str:
    """
    Sanitize text for HTML display (XSS prevention).

    Args:
        text: Raw text to display

    Returns:
        HTML-escaped text
    """
    if not text:
        return ""

    return html.escape(str(text), quote=True)


def validate_score(score: Any) -> bool:
    """
    Validate analysis score.

    Args:
        score: Score value to validate

    Returns:
        True if valid
    """
    if not isinstance(score, int):
        return False
    from backend.constants import SCORE_MAX, SCORE_MIN

    return SCORE_MIN <= score <= SCORE_MAX


def validate_email(email: str) -> bool:
    """
    Validate email address format.

    Args:
        email: Email to validate

    Returns:
        True if valid email format
    """
    if not email or not isinstance(email, str):
        return False

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email.strip()))


def validate_password_strength(password: str) -> tuple[bool, list[str]]:
    """
    Validate password strength.

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    if len(password) < 8:
        errors.append("Password must be at least 8 characters")
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain lowercase letter")
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain uppercase letter")
    if not re.search(r"[0-9]", password):
        errors.append("Password must contain number")

    return len(errors) == 0, errors


def generate_safe_slug(text: str) -> str:
    """
    Generate URL-safe slug from text.

    Args:
        text: Source text

    Returns:
        URL-safe slug
    """
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s-]+", "-", text)
    text = text.strip("-")
    return text[:50]


def deep_sanitize_dict(data: dict[str, Any], max_depth: int = 5) -> dict[str, Any]:
    """
    Recursively sanitize dictionary values.

    Args:
        data: Dictionary to sanitize
        max_depth: Maximum recursion depth

    Returns:
        Sanitized dictionary
    """
    if max_depth <= 0:
        return {}

    sanitized = {}
    for key, value in data.items():
        safe_key = sanitize_string(str(key))
        if isinstance(value, dict):
            sanitized[safe_key] = deep_sanitize_dict(value, max_depth - 1)
        elif isinstance(value, list):
            sanitized[safe_key] = [
                deep_sanitize_dict(v, max_depth - 1)
                if isinstance(v, dict)
                else sanitize_string(str(v))
                for v in value
            ]
        else:
            sanitized[safe_key] = sanitize_string(str(value))

    return sanitized


def is_safe_content_type(content_type: str | None) -> bool:
    """
    Check if content type is allowed.

    Args:
        content_type: MIME type to check

    Returns:
        True if allowed
    """
    from backend.constants import ALLOWED_CONTENT_TYPES

    if not content_type:
        return False

    return content_type.strip() in ALLOWED_CONTENT_TYPES
