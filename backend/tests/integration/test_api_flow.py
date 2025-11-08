"""
Integration tests for complete API flow.
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.models.tutor import Tutor

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


def test_complete_session_flow(client, db_session, api_key):
    """Test complete flow: create session -> process -> update scores."""
    # Create tutor
    tutor = Tutor(
        name="Test Tutor",
        is_active=True
    )
    db_session.add(tutor)
    db_session.commit()
    
    session_id = uuid4()
    
    # Mock Celery tasks
    with patch('app.api.sessions.process_session.delay') as mock_process, \
         patch('app.tasks.session_processor.send_email_report.delay') as mock_email, \
         patch('app.services.email_report_service.get_email_service') as mock_email_service:
        
        mock_process.return_value = None
        mock_email.return_value = None
        
        # Mock email service to succeed
        mock_email_instance = mock_email_service.return_value
        mock_email_instance.send_email.return_value = True
        
        # 1. Create session via API
        response = client.post(
            "/api/sessions",
            headers={"X-API-Key": api_key},
            json={
                "session_id": str(session_id),
                "tutor_id": str(tutor.id),
                "student_id": "student_123",
                "scheduled_time": datetime.utcnow().isoformat(),
                "completed_time": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
                "status": "completed",
                "duration_minutes": 60
            }
        )
        
        assert response.status_code == 202
        
        # 2. Manually trigger processing (simulating Celery task)
        from app.tasks.session_processor import process_session
        result = process_session(str(session_id))
        
        assert result["status"] == "success"
        
        # 3. Verify scores were updated
        from app.models.tutor_score import TutorScore
        score = db_session.query(TutorScore).filter(TutorScore.tutor_id == tutor.id).first()
        assert score is not None
        
        # 4. Verify tutor appears in list
        # Use a large limit to ensure we get all tutors (including the one we just created)
        response = client.get("/api/tutors?limit=1000")
        assert response.status_code == 200
        data = response.json()
        tutor_ids = [t["id"] for t in data["tutors"]]
        assert str(tutor.id) in tutor_ids, f"Tutor {tutor.id} not found in {len(tutor_ids)} tutors. Total: {data.get('total', 'unknown')}"


def test_session_with_reschedule_flow(client, db_session, api_key):
    """Test flow with rescheduled session."""
    tutor = Tutor(name="Test Tutor", is_active=True)
    db_session.add(tutor)
    db_session.commit()
    
    session_id = uuid4()
    original_time = datetime.utcnow()
    new_time = original_time + timedelta(days=1)
    
    with patch('app.api.sessions.process_session.delay') as mock_process, \
         patch('app.tasks.session_processor.send_email_report.delay'):
        
        mock_process.return_value = None
        
        # Create rescheduled session
        response = client.post(
            "/api/sessions",
            headers={"X-API-Key": api_key},
            json={
                "session_id": str(session_id),
                "tutor_id": str(tutor.id),
                "student_id": "student_123",
                "scheduled_time": original_time.isoformat(),
                "status": "rescheduled",
                "reschedule_info": {
                    "initiator": "tutor",
                    "original_time": original_time.isoformat(),
                    "new_time": new_time.isoformat(),
                    "reason": "Emergency",
                    "cancelled_at": (original_time - timedelta(hours=12)).isoformat()
                }
            }
        )
        
        assert response.status_code == 202
        
        # Process session
        from app.tasks.session_processor import process_session
        result = process_session(str(session_id))
        
        assert result["status"] == "success"
        
        # Verify reschedule was created
        from app.models.session import Session as SessionModel
        session = db_session.query(SessionModel).filter(SessionModel.id == session_id).first()
        assert session.reschedule is not None
        assert session.reschedule.initiator == "tutor"

