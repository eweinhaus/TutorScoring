"""
Tests for session ingestion endpoints.
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from app.models.session import Session as SessionModel
from app.models.tutor import Tutor
from app.models.reschedule import Reschedule

@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def api_key():
    """API key for authenticated requests."""
    import os
    os.environ["API_KEY"] = "test-api-key"
    return "test-api-key"


def test_create_session_success(client, db_session, sample_tutor, api_key, monkeypatch):
    """Test successful session creation."""
    session_id = uuid4()
    tutor_id = sample_tutor.id
    
    # Mock Celery task
    with patch('app.api.sessions.process_session.delay') as mock_task:
        mock_task.return_value = None
        
        response = client.post(
            "/api/sessions",
            headers={"X-API-Key": api_key},
            json={
                "session_id": str(session_id),
                "tutor_id": str(tutor_id),
                "student_id": "student_123",
                "scheduled_time": datetime.utcnow().isoformat(),
                "completed_time": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
                "status": "completed",
                "duration_minutes": 60
            }
        )
        
        assert response.status_code == 202
        data = response.json()
        assert data["id"] == str(session_id)
        assert data["tutor_id"] == str(tutor_id)
        assert data["status"] == "completed"
        
        # Verify Celery task was queued
        mock_task.assert_called_once()
        
        # Verify session was created in database
        session = db_session.query(SessionModel).filter(SessionModel.id == session_id).first()
        assert session is not None


def test_create_session_with_reschedule(client, db_session, sample_tutor, api_key, monkeypatch):
    """Test session creation with reschedule info."""
    session_id = uuid4()
    tutor_id = sample_tutor.id
    original_time = datetime.utcnow()
    new_time = original_time + timedelta(days=1)
    
    with patch('app.api.sessions.process_session.delay') as mock_task:
        mock_task.return_value = None
        
        response = client.post(
            "/api/sessions",
            headers={"X-API-Key": api_key},
            json={
                "session_id": str(session_id),
                "tutor_id": str(tutor_id),
                "student_id": "student_123",
                "scheduled_time": original_time.isoformat(),
                "status": "rescheduled",
                "reschedule_info": {
                    "initiator": "tutor",
                    "original_time": original_time.isoformat(),
                    "new_time": new_time.isoformat(),
                    "reason": "Personal emergency",
                    "cancelled_at": (original_time - timedelta(hours=12)).isoformat()
                }
            }
        )
        
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "rescheduled"
        
        # Verify reschedule was created
        session = db_session.query(SessionModel).filter(SessionModel.id == session_id).first()
        assert session is not None
        assert session.reschedule is not None
        assert session.reschedule.initiator == "tutor"


def test_create_session_missing_reschedule_info(client, db_session, sample_tutor, api_key):
    """Test session creation fails when rescheduled status but no reschedule_info."""
    session_id = uuid4()
    tutor_id = sample_tutor.id
    
    response = client.post(
        "/api/sessions",
        headers={"X-API-Key": api_key},
        json={
            "session_id": str(session_id),
            "tutor_id": str(tutor_id),
            "student_id": "student_123",
            "scheduled_time": datetime.utcnow().isoformat(),
            "status": "rescheduled"
            # Missing reschedule_info
        }
    )
    
    assert response.status_code == 400


def test_create_session_duplicate_id(client, db_session, sample_tutor, api_key, monkeypatch):
    """Test session creation fails with duplicate session_id."""
    session_id = uuid4()
    tutor_id = sample_tutor.id
    
    # Create first session
    with patch('app.api.sessions.process_session.delay'):
        client.post(
            "/api/sessions",
            headers={"X-API-Key": api_key},
            json={
                "session_id": str(session_id),
                "tutor_id": str(tutor_id),
                "student_id": "student_123",
                "scheduled_time": datetime.utcnow().isoformat(),
                "status": "completed"
            }
        )
    
    # Try to create duplicate
    response = client.post(
        "/api/sessions",
        headers={"X-API-Key": api_key},
        json={
            "session_id": str(session_id),
            "tutor_id": str(tutor_id),
            "student_id": "student_456",
            "scheduled_time": datetime.utcnow().isoformat(),
            "status": "completed"
        }
    )
    
    assert response.status_code == 400


def test_create_session_unauthorized(client, db_session, sample_tutor):
    """Test session creation fails without API key."""
    session_id = uuid4()
    tutor_id = sample_tutor.id
    
    response = client.post(
        "/api/sessions",
        json={
            "session_id": str(session_id),
            "tutor_id": str(tutor_id),
            "student_id": "student_123",
            "scheduled_time": datetime.utcnow().isoformat(),
            "status": "completed"
        }
    )
    
    assert response.status_code == 401


def test_create_session_invalid_data(client, db_session, sample_tutor, api_key):
    """Test session creation fails with invalid data."""
    response = client.post(
        "/api/sessions",
        headers={"X-API-Key": api_key},
        json={
            "session_id": "not-a-uuid",
            "tutor_id": str(sample_tutor.id),
            "student_id": "",
            "scheduled_time": "invalid-date",
            "status": "invalid_status"
        }
    )
    
    assert response.status_code == 422  # Validation error

