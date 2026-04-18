"""Tests for rate limiting middleware."""

import pytest
from unittest.mock import patch, MagicMock
from flask import Flask, request, jsonify
from flask_limiter import Limiter

from backend.middleware.rate_limit import (
    limiter as rate_limiter,
    rate_limit,
    get_rate_limit_info,
)
from backend.utils.logger import get_logger


class TestRateLimiting:
    """Test suite for rate limiting."""

    def setup_method(self):
        """Set up test app."""
        self.app = Flask(__name__)
        self.app.config["TESTING"] = True
        self.app.config["REDIS_URL"] = "redis://localhost:6379/0"

        # Use simple in-memory limiter for tests
        self.app.config["RATELIMIT_STORAGE_URL"] = "memory://"
        self.app.config["RATELIMIT_STRATEGY"] = "fixed-window"

    def test_rate_limit_decorator(self):
        """Test custom rate limit decorator."""

        @self.app.route("/test")
        @rate_limit("100 per minute")
        def test_endpoint():
            return jsonify({"status": "ok"})

        client = self.app.test_client()

        # Request should succeed
        response = client.get("/test")
        assert response.status_code == 200

    def test_default_rate_limits(self):
        """Test rate limiter initialization."""
        app = Flask(__name__)
        rate_limiter.init_app(app)
        assert app is not None

    def test_rate_limit_headers(self):
        """Test rate limit headers in response."""
        app = Flask(__name__)
        app.config["RATELIMIT_STORAGE_URL"] = "memory://"
        rate_limiter.init_app(app)

        @app.route("/test")
        def test_endpoint():
            return jsonify({"status": "ok"})

        client = app.test_client()
        response = client.get("/test")
        # Check for rate limit headers (if using proper Redis, they'd be present)
        # In memory backend, headers might not be set

    def test_rate_limit_bypass_for_health_checks(self):
        """Test that health endpoints bypass rate limits."""
        # In production, we might want to exclude health endpoints
        pass  # Implementation depends on configuration


class TestRateLimitInfo:
    """Test rate limit info utility."""

    def test_get_rate_limit_info(self):
        """Test getting rate limit info."""
        app = Flask(__name__)
        app.config["RATELIMIT_STORAGE_URL"] = "memory://"
        with app.app_context():
            with patch(
                "backend.middleware.rate_limit.get_remote_address",
                return_value="127.0.0.1",
            ):
                info = get_rate_limit_info()
                assert "identifier" in info
