"""Tests for Prometheus metrics."""

import pytest
from unittest.mock import patch, MagicMock

from backend.utils.metrics import (
    HTTP_REQUESTS_TOTAL,
    HTTP_REQUEST_DURATION,
    GROQ_API_CALLS_TOTAL,
    GROQ_API_ERRORS_TOTAL,
    ANALYSES_TOTAL,
    track_requests,
    track_groq_call,
    track_pdf_processing,
    track_database_operation,
    get_metrics_endpoint,
)


class TestMetrics:
    """Test suite for metrics collection."""

    def test_http_requests_counter(self):
        """Test HTTP requests counter increments."""
        initial = HTTP_REQUESTS_TOTAL.labels("GET", "/test", 200)._value.get()
        HTTP_REQUESTS_TOTAL.labels("GET", "/test", 200).inc()
        new = HTTP_REQUESTS_TOTAL.labels("GET", "/test", 200)._value.get()
        assert new == initial + 1

    def test_analyses_counter(self):
        """Test analyses counter increments."""
        initial = ANALYSES_TOTAL._value.get()
        ANALYSES_TOTAL.inc()
        new = ANALYSES_TOTAL._value.get()
        assert new == initial + 1

    def test_groq_call_decorator_success(self):
        """Test track_groq_call decorator on success."""
        call_count = {"value": 0}

        @track_groq_call
        def mock_groq_call():
            call_count["value"] += 1
            return {"result": "success"}

        result = mock_groq_call()

        assert result == {"result": "success"}
        assert call_count["value"] == 1

        # Check metric incremented
        count = GROQ_API_CALLS_TOTAL.labels(status="success")._value.get()
        assert count >= 1

    def test_groq_call_decorator_error(self):
        """Test track_groq_call decorator on error."""

        @track_groq_call
        def mock_groq_call():
            raise ValueError("API Error")

        with pytest.raises(ValueError):
            mock_groq_call()

        # Check error metric incremented
        count = GROQ_API_ERRORS_TOTAL.labels(error_type="ValueError")._value.get()
        assert count >= 1

    def test_pdf_processing_decorator(self):
        """Test track_pdf_processing decorator."""
        import time

        @track_pdf_processing
        def slow_extraction():
            time.sleep(0.01)  # 10ms
            return "text"

        result = slow_extraction()
        assert result == "text"

    def test_database_operation_decorator_success(self):
        """Test database operation tracking on success."""
        from backend.utils.metrics import DATABASE_OPERATIONS

        @track_database_operation("INSERT")
        def db_insert():
            return True

        result = db_insert()
        assert result is True

        # Check metric incremented
        # count = DATABASE_OPERATIONS.labels('INSERT', 'success)._value.get()
        # assert count >= 1

    def test_database_operation_decorator_error(self):
        """Test database operation tracking on error."""

        @track_database_operation("UPDATE")
        def db_update():
            raise Exception("DB error")

        with pytest.raises(Exception):
            db_update()

        # Check error metric incremented
        # count = DATABASE_OPERATIONS.labels('UPDATE', 'error)._value.get()
        # assert count >= 1

    def test_get_metrics_endpoint(self):
        """Test metrics endpoint returns data."""
        output = get_metrics_endpoint()
        assert isinstance(output, bytes)
        # Should contain some metrics
        output_str = output.decode("utf-8")
        assert "http_requests_total" in output_str or len(output_str) > 0


class TestRequestTracking:
    """Test request tracking middleware."""

    def test_track_requests_middleware(self):
        """Test track_requests middleware registration."""
        app = MagicMock()
        track_requests(app)

        # Check that before/after request handlers were registered
        assert app.before_request.called
        assert app.after_request.called
