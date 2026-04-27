"""Centralized configuration management using environment variables.

All configuration values are loaded from environment variables with
sensible defaults for development. Production deployments should
provide explicit values via environment.
"""

from dataclasses import dataclass, field
import os
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class DatabaseConfig:
    """Database connection settings."""

    url: str = os.getenv("DATABASE_URL", "sqlite:///resumeai.db")
    echo: bool = False


@dataclass(frozen=True)
class RedisConfig:
    """Redis connection settings for rate limiting and caching."""

    url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    socket_connect_timeout: int = 2


@dataclass(frozen=True)
class RateLimitConfig:
    """Rate limiting configuration."""

    # Default limits (requests per time window)
    default_per_day: int = int(os.getenv("RATELIMIT_PER_DAY", "100"))
    default_per_hour: int = int(os.getenv("RATELIMIT_PER_HOUR", "20"))

    # Storage backend
    storage_url: str = os.getenv("RATELIMIT_STORAGE_URL", "memory://")
    strategy: str = "fixed-window"

    # Development overrides
    dev_limit: str = "1000 per hour"


@dataclass(frozen=True)
class FlaskConfig:
    """Flask application settings."""

    env: str = os.getenv("FLASK_ENV", "production")
    debug: bool = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    testing: bool = os.getenv("FLASK_TESTING", "False").lower() == "true"
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-key-CHANGE-ME")


@dataclass(frozen=True)
class AIConfig:
    """AI service configuration."""

    groq_api_key: Optional[str] = os.getenv("GROQ_API_KEY")
    model: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    temperature: float = float(os.getenv("AI_TEMPERATURE", "0.3"))
    max_tokens: int = int(os.getenv("AI_MAX_TOKENS", "2048"))


@dataclass(frozen=True)
class FileUploadConfig:
    """File upload security and limits."""

    max_size_bytes: int = int(os.getenv("MAX_FILE_SIZE", str(5 * 1024 * 1024)))  # 5MB
    max_text_length: int = int(os.getenv("MAX_TEXT_LENGTH", "3000"))
    allowed_extensions: Tuple[str, ...] = (".pdf",)


@dataclass(frozen=True)
class SecurityConfig:
    """Security headers and settings."""

    # CSP (Content Security Policy)
    csp_default_src: str = os.getenv("CSP_DEFAULT_SRC", "'self'")
    csp_script_src: str = os.getenv("CSP_SCRIPT_SRC", "'self'")
    csp_style_src: str = os.getenv("CSP_STYLE_SRC", "'self'")
    csp_img_src: str = os.getenv("CSP_IMG_SRC", "'self' data:")
    csp_connect_src: str = os.getenv("CSP_CONNECT_SRC", "'self'")
    csp_font_src: str = os.getenv("CSP_FONT_SRC", "'self'")
    csp_object_src: str = os.getenv("CSP_OBJECT_SRC", "'none'")
    csp_media_src: str = os.getenv("CSP_MEDIA_SRC", "'self'")
    csp_frame_src: str = os.getenv("CSP_FRAME_SRC", "'none'")
    csp_base_uri: str = os.getenv("CSP_BASE_URI", "'self'")
    csp_form_action: str = os.getenv("CSP_FORM_ACTION", "'self'")
    csp_report_uri: str = os.getenv("CSP_REPORT_URI", "")

    # HSTS (HTTP Strict Transport Security)
    hsts_max_age: int = int(os.getenv("HSTS_MAX_AGE", "31536000"))  # 1 year
    hsts_include_subdomains: bool = os.getenv("HSTS_INCLUDE_SUBDOMAINS", "true").lower() == "true"
    hsts_preload: bool = os.getenv("HSTS_PRELOAD", "false").lower() == "true"

    # Other security headers
    x_frame_options: str = os.getenv("X_FRAME_OPTIONS", "DENY")
    x_content_type_options: str = os.getenv("X_CONTENT_TYPE_OPTIONS", "nosniff")
    x_xss_protection: str = os.getenv("X_XSS_PROTECTION", "1; mode=block")
    referrer_policy: str = os.getenv("REFERRER_POLICY", "strict-origin-when-cross-origin")
    permissions_policy: str = os.getenv("PERMISSIONS_POLICY", "camera=(), microphone=(), geolocation=()")
    x_permitted_cross_domain_policies: str = os.getenv("X_PERMITTED_CROSS_DOMAIN_POLICIES", "none")

    # Content type options
    content_type_nosniff: bool = True

    # Request size limits
    max_content_length: int = int(os.getenv("MAX_CONTENT_LENGTH", str(16 * 1024 * 1024)))  # 16MB default
    max_body_size: int = int(os.getenv("MAX_BODY_SIZE", str(16 * 1024 * 1024)))  # 16MB

    # Cookie security (for future auth)
    cookie_httponly: bool = True
    cookie_secure: bool = os.getenv("COOKIE_SECURE", "true").lower() == "true"
    cookie_samesite: str = os.getenv("COOKIE_SAMESITE", "Lax")


@dataclass(frozen=True)
class MonitoringConfig:
    """Monitoring and metrics configuration."""

    prometheus_enabled: bool = os.getenv("PROMETHEUS_ENABLED", "True").lower() == "true"
    metrics_path: str = os.getenv("METRICS_PATH", "/metrics")
    include_debug_metrics: bool = os.getenv("INCLUDE_DEBUG_METRICS", "false").lower() == "true"


# Instantiate configuration objects
db_config = DatabaseConfig()
redis_config = RedisConfig()
rate_limit_config = RateLimitConfig()
flask_config = FlaskConfig()
ai_config = AIConfig()
file_config = FileUploadConfig()
security_config = SecurityConfig()
monitoring_config = MonitoringConfig()
