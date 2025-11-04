"""
Tests for health check endpoint.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app

@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


def test_health_check_success(client, db_session, monkeypatch):
    """Test health check endpoint returns healthy status."""
    # Mock database connection
    def mock_get_db():
        yield db_session
    
    monkeypatch.setattr("app.api.health.get_db", mock_get_db)
    
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "database" in data
    assert "version" in data


def test_health_check_includes_all_statuses(client, db_session, monkeypatch):
    """Test health check includes database and Redis status."""
    def mock_get_db():
        yield db_session
    
    monkeypatch.setattr("app.api.health.get_db", mock_get_db)
    
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "database" in data
    assert "redis" in data

