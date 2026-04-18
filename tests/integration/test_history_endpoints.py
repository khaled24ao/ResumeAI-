"""Integration tests for history endpoints."""

import pytest
import json
from datetime import datetime
from unittest.mock import patch, MagicMock

from backend.app import create_app
from backend.services.database import get_db_context
from backend.models import Analysis


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def sample_analysis_in_db(client):
    """Create a sample analysis in database."""
    with get_db_context() as db:
        analysis = Analysis(
            filename="test.pdf",
            score=8,
            strengths='["Python", "Flask"]',
            weaknesses='["Testing"]',
            improved_summary="Experienced developer",
            keywords_missing='["Docker", "AWS"]',
            file_size=1024,
            processing_time_ms=1500
        )
        db.add(analysis)
        db.flush()
        analysis_id = analysis.id
    return analysis_id


class TestHistoryEndpoints:
    """Integration tests for history API endpoints."""

    def test_get_history_empty(self, client):
        """Test getting empty history."""
        # Assuming empty database or mocking
        with patch('backend.routes.history.get_db_context') as mock_db:
            mock_session = MagicMock()
            mock_session.query.return_value.offset.return_value.limit.return_value.all.return_value = []
            mock_session.query.return_value.count.return_value = 0
            mock_db.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_db.return_value.__exit__ = MagicMock(return_value=None)
            
            response = client.get('/api/v1/history')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'analyses' in data
            assert data['total'] == 0

    def test_get_history_with_results(self, client):
        """Test getting history with results."""
        mock_analysis = MagicMock()
        mock_analysis.id = 1
        mock_analysis.filename = "test.pdf"
        mock_analysis.score = 8
        mock_analysis.created_at = datetime.utcnow()
        mock_analysis.processing_time_ms = 1500
        
        with patch('backend.routes.history.get_db_context') as mock_db:
            mock_session = MagicMock()
            mock_session.query.return_value.offset.return_value.limit.return_value.all.return_value = [mock_analysis]
            mock_session.query.return_value.count.return_value = 1
            mock_db.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_db.return_value.__exit__ = MagicMock(return_value=None)
            
            response = client.get('/api/v1/history')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data['analyses']) == 1

    def test_get_analysis_by_id(self, client):
        """Test getting single analysis."""
        mock_analysis = MagicMock()
        mock_analysis.id = 1
        mock_analysis.filename = "test.pdf"
        mock_analysis.score = 7
        mock_analysis.improved_summary = "Good candidate"
        mock_analysis.strengths_list = ["Skill 1", "Skill 2"]
        mock_analysis.weaknesses_list = ["Weak 1"]
        mock_analysis.keywords_missing_list = ["Python", "Docker"]
        mock_analysis.created_at = datetime.utcnow()
        mock_analysis.processing_time_ms = 1000
        
        with patch('backend.routes.history.get_db_context') as mock_db:
            mock_session = MagicMock()
            mock_session.query.return_value.filter.return_value.first.return_value = mock_analysis
            mock_db.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_db.return_value.__exit__ = MagicMock(return_value=None)
            
            response = client.get('/api/v1/history/1')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['id'] == 1
            assert 'strengths' in data
            assert 'weaknesses' in data

    def test_get_nonexistent_analysis(self, client):
        """Test getting analysis that doesn't exist."""
        with patch('backend.routes.history.get_db_context') as mock_db:
            mock_session = MagicMock()
            mock_session.query.return_value.filter.return_value.first.return_value = None
            mock_db.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_db.return_value.__exit__ = MagicMock(return_value=None)
            
            response = client.get('/api/v1/history/999')
            assert response.status_code == 404
            data = json.loads(response.data)
            assert 'error' in data

    def test_delete_analysis(self, client):
        """Test deleting analysis."""
        mock_analysis = MagicMock()
        
        with patch('backend.routes.history.get_db_context') as mock_db:
            mock_session = MagicMock()
            mock_session.query.return_value.filter.return_value.first.return_value = mock_analysis
            mock_db.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_db.return_value.__exit__ = MagicMock(return_value=None)
            
            response = client.delete('/api/v1/history/1')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'message' in data
            mock_session.delete.assert_called_once_with(mock_analysis)

    def test_delete_nonexistent_analysis(self, client):
        """Test deleting analysis that doesn't exist."""
        with patch('backend.routes.history.get_db_context') as mock_db:
            mock_session = MagicMock()
            mock_session.query.return_value.filter.return_value.first.return_value = None
            mock_db.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_db.return_value.__exit__ = MagicMock(return_value=None)
            
            response = client.delete('/api/v1/history/999')
            assert response.status_code == 404

    def test_get_stats(self, client):
        """Test getting analytics statistics."""
        with patch('backend.routes.history.get_db_context') as mock_db:
            mock_session = MagicMock()
            mock_session.query.return_value.count.return_value = 10
            mock_session.query.return_value.scalar.side_effect = [8.5, 10, 5]
            
            # Mock keyword analysis
            analyses = [
                (json.dumps(["Python", "Docker"]),),
                (json.dumps(["Python", "AWS"]),),
                (json.dumps(["Docker"]),),
            ]
            mock_session.query.return_value.limit.return_value.all.return_value = analyses
            
            mock_db.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_db.return_value.__exit__ = MagicMock(return_value=None)
            
            response = client.get('/api/v1/history/stats')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'total_analyses' in data
            assert 'average_score' in data
            assert 'top_keywords' in data
            assert data['total_analyses'] == 10
            assert data['average_score'] == 8.5

    def test_history_pagination(self, client):
        """Test history endpoint pagination."""
        with patch('backend.routes.history.get_db_context') as mock_db:
            mock_session = MagicMock()
            mock_session.query.return_value.offset.return_value.limit.return_value.all.return_value = []
            mock_session.query.return_value.count.return_value = 50
            mock_db.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_db.return_value.__exit__ = MagicMock(return_value=None)
            
            response = client.get('/api/v1/history?page=2&per_page=10')
            assert response.status_code == 200
            
            # Verify offset was calculated correctly
            offset_call = mock_session.query.return_value.offset.call_args
            assert offset_call[0][0] == 10  # (page-1) * per_page