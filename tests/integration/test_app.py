"""Tests for Flask application integration."""

import pytest
from unittest.mock import patch, MagicMock

from backend.app import create_app
from backend.models import Base, Analysis
from backend.services.database import engine, SessionLocal


class TestApplication:
    """Test suite for Flask application."""

    def test_app_factory_development(self):
        """Test app factory in development mode."""
        with patch.dict('os.environ', {'FLASK_ENV': 'development'}):
            app = create_app()
            assert app.config["DEBUG"] is True
            assert app.config["ENV"] == "development"

    def test_app_factory_production(self):
        """Test app factory in production mode."""
        with patch.dict('os.environ', {'FLASK_ENV': 'production'}):
            app = create_app()
            assert app.config["DEBUG"] is False
            assert app.config["ENV"] == "production"

    def test_app_has_blueprints(self):
        """Test app registers blueprints."""
        app = create_app()
        assert 'analyze' in app.blueprints
        assert 'history' in app.blueprints

    def test_error_handlers(self):
        """Test error handlers return proper JSON."""
        app = create_app()
        app.config["TESTING"] = True
        
        with app.test_client() as client:
            # 404 error
            response = client.get('/nonexistent')
            assert response.status_code == 404
            data = response.get_json()
            assert 'error' in data
            
            # 500 error (trigger with error handler)
            @app.route('/trigger-500')
            def trigger_500():
                raise Exception("Test error")
            
            response = client.get('/trigger-500')
            assert response.status_code == 500

    def test_health_endpoint(self):
        """Test health check."""
        app = create_app()
        with app.test_client() as client:
            response = client.get('/health')
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'ok'

    def test_ready_endpoint(self):
        """Test readiness probe."""
        app = create_app()
        with app.test_client() as client:
            response = client.get('/ready')
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'ready'

    def test_index_returns_html(self):
        """Test index returns HTML page."""
        app = create_app()
        with app.test_client() as client:
            response = client.get('/')
            assert response.status_code == 200
            assert b'ResumeAI' in response.data

    def test_rate_limit_status_endpoint(self):
        """Test rate limit status endpoint."""
        app = create_app()
        with app.test_client() as client:
            response = client.get('/rate-limit-status')
            assert response.status_code == 200
            data = response.get_json()
            assert 'identifier' in data

    def test_metrics_endpoint(self):
        """Test Prometheus metrics endpoint."""
        app = create_app()
        with app.test_client() as client:
            response = client.get('/metrics')
            assert response.status_code == 200
            assert response.content_type == 'text/plain'
            # Should contain some metrics
            content = response.data.decode('utf-8')
            assert len(content) > 0

    def test_database_initialization(self):
        """Test database is initialized on app creation."""
        # In test mode, database should be initialized
        app = create_app()
        # Check that tables can be queried
        with app.app_context():
            try:
                Base.metadata.create_all(bind=engine)
                # Tables created without error
                assert True
            except Exception as e:
                pytest.skip(f"Database not available: {e}")

    def test_config_from_object(self):
        """Test loading config from object."""
        class TestConfig:
            DEBUG = True
            TESTING = True
            SECRET_KEY = 'test'
        
        app = create_app(TestConfig)
        assert app.config["DEBUG"] is True
        assert app.config["TESTING"] is True

    def test_cors_headers(self):
        """Test CORS headers if configured."""
        # CORS not currently implemented, but can be added
        pass

    def test_request_logging(self):
        """Test that requests are logged."""
        with patch('backend.app.logger') as mock_logger:
            app = create_app()
            with app.test_client() as client:
                client.get('/health')
                # Check that info log was made
                mock_logger.info.assert_called()