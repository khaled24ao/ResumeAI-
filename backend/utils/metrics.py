"""Prometheus metrics collection and exposition."""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
import time
from functools import wraps
from typing import Callable

from flask import request, g

from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Metrics
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status"],
)

HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

GROQ_API_CALLS_TOTAL = Counter(
    "groq_api_calls_total", "Total number of Groq API calls", ["status"]
)

GROQ_API_ERRORS_TOTAL = Counter(
    "groq_api_errors_total", "Total number of Groq API errors", ["error_type"]
)

PDF_PROCESSING_DURATION = Histogram(
    "pdf_processing_duration_seconds",
    "PDF text extraction duration",
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
)

ANALYSES_TOTAL = Counter("analyses_total", "Total number of resume analyses completed")

DATABASE_OPERATIONS = Counter(
    "database_operations_total", "Database operations count", ["operation", "status"]
)

# Active requests gauge
ACTIVE_REQUESTS = Gauge("active_requests", "Number of currently active HTTP requests")


def track_requests(app):
    """
    Middleware to track all HTTP requests.

    Usage:
        from backend.utils.metrics import track_requests
        track_requests(app)
    """

    @app.before_request
    def before_request():
        g.start_time = time.time()
        ACTIVE_REQUESTS.inc()

    @app.after_request
    def after_request(response):
        if hasattr(g, "start_time"):
            duration = time.time() - g.start_time
            endpoint = request.endpoint or "unknown"
            HTTP_REQUEST_DURATION.labels(endpoint=endpoint).observe(duration)
            HTTP_REQUESTS_TOTAL.labels(
                method=request.method, endpoint=endpoint, status=response.status_code
            ).inc()
            ACTIVE_REQUESTS.dec()
        return response


def track_groq_call(f: Callable) -> Callable:
    """
    Decorator to track Groq API calls.

    Usage:
        @track_groq_call
        def call_groq():
            ...
    """

    @wraps(f)
    def wrapped(*args, **kwargs):
        try:
            result = f(*args, **kwargs)
            GROQ_API_CALLS_TOTAL.labels(status="success").inc()
            return result
        except Exception as e:
            GROQ_API_ERRORS_TOTAL.labels(error_type=type(e).__name__).inc()
            raise

    return wrapped


def track_pdf_processing(f: Callable) -> Callable:
    """
    Decorator to track PDF processing time.

    Usage:
        @track_pdf_processing
        def extract_text(file):
            ...
    """

    @wraps(f)
    def wrapped(*args, **kwargs):
        start = time.time()
        try:
            result = f(*args, **kwargs)
            duration = time.time() - start
            PDF_PROCESSING_DURATION.observe(duration)
            return result
        except Exception:
            raise

    return wrapped


def increment_analyses_counter():
    """Increment total analyses counter."""
    ANALYSES_TOTAL.inc()


def track_database_operation(operation: str):
    """
    Decorator to track database operations.

    Usage:
        @track_database_operation('INSERT')
        def save_to_db():
            ...
    """

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapped(*args, **kwargs):
            try:
                result = f(*args, **kwargs)
                DATABASE_OPERATIONS.labels(operation=operation, status="success").inc()
                return result
            except Exception:
                DATABASE_OPERATIONS.labels(operation=operation, status="error").inc()
                raise

        return wrapped

    return decorator


def get_metrics_endpoint():
    """
    Return Prometheus metrics for /metrics endpoint.

    Returns:
        bytes: Prometheus-format metrics
    """
    return generate_latest(REGISTRY)
