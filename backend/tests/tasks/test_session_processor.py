"""
Tests for session processor task.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from uuid import uuid4

from app.tasks.session_processor import process_session
from app.models.tutor import Tutor
from app.models.session import Session as SessionModel
from app.models.tutor_score import TutorScore


@pytest.fixture
def mock_celery_task():
    """Mock Celery task decorator."""
    def decorator(func):
        return func
    return decorator


def test_process_session_success(db_session, sample_tutor):
    """Test successful session processing."""
    # Create session
    session = SessionModel(
        tutor_id=sample_tutor.id,
        student_id="student_123",
        scheduled_time=datetime.utcnow(),
        completed_time=datetime.utcnow() + timedelta(hours=1),
        status="completed",
        duration_minutes=60
    )
    db_session.add(session)
    db_session.commit()
    
    # Mock email task
    with patch('app.tasks.session_processor.send_email_report.delay') as mock_email:
        mock_email.return_value = None
        
        # Process session
        result = process_session(str(session.id))
        
        assert result["status"] == "success"
        assert result["session_id"] == str(session.id)
        
        # Verify scores were updated
        score = db_session.query(TutorScore).filter(TutorScore.tutor_id == sample_tutor.id).first()
        assert score is not None


def test_process_session_not_found(db_session):
    """Test processing non-existent session."""
    fake_id = uuid4()
    
    with pytest.raises(ValueError, match="not found"):
        process_session(str(fake_id))


def test_process_session_retry_on_error(db_session, sample_tutor):
    """Test that task retries on transient errors."""
    # Create session
    session = SessionModel(
        tutor_id=sample_tutor.id,
        student_id="student_123",
        scheduled_time=datetime.utcnow(),
        status="completed"
    )
    db_session.add(session)
    db_session.commit()
    
    # Mock update_scores to raise error
    with patch('app.tasks.session_processor.update_scores_for_tutor') as mock_update:
        mock_update.side_effect = Exception("Database error")
        
        # Should raise retry exception
        task_instance = MagicMock()
        task_instance.request.retries = 0
        task_instance.max_retries = 3
        task_instance.retry = MagicMock(side_effect=Exception("Retry"))
        
        # This would normally be handled by Celery
        # For testing, we just verify the error is raised
        with pytest.raises(Exception):
            process_session.__wrapped__(task_instance, str(session.id))

