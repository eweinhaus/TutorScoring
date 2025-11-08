"""
Tests for email tasks.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from uuid import uuid4

from app.tasks.email_tasks import send_email_report
from app.models.session import Session as SessionModel
from app.models.tutor import Tutor
from app.models.email_report import EmailReport


def test_send_email_report_success(db_session, sample_tutor):
    """Test successful email sending."""
    # Create session
    session = SessionModel(
        tutor_id=sample_tutor.id,
        student_id="student_123",
        scheduled_time=datetime.utcnow(),
        status="completed"
    )
    db_session.add(session)
    db_session.commit()
    
    # Mock email service
    with patch('app.tasks.email_tasks.send_session_report') as mock_send:
        mock_send.return_value = True
        
        import os
        os.environ["ADMIN_EMAIL"] = "admin@test.com"
        
        result = send_email_report(str(session.id))
        
        assert result["status"] == "success"
        
        # Verify EmailReport was created
        email_report = db_session.query(EmailReport).filter(
            EmailReport.session_id == session.id
        ).first()
        assert email_report is not None
        assert email_report.status == "sent"


def test_send_email_report_failure(db_session, sample_tutor):
    """Test email sending failure."""
    # Create session
    session = SessionModel(
        tutor_id=sample_tutor.id,
        student_id="student_123",
        scheduled_time=datetime.utcnow(),
        status="completed"
    )
    db_session.add(session)
    db_session.commit()
    
    # Mock email service to fail
    with patch('app.tasks.email_tasks.send_session_report') as mock_send:
        mock_send.return_value = False
        
        import os
        os.environ["ADMIN_EMAIL"] = "admin@test.com"
        
        result = send_email_report(str(session.id))
        
        assert result["status"] == "failed"
        
        # Verify EmailReport was created with failed status
        email_report = db_session.query(EmailReport).filter(
            EmailReport.session_id == session.id
        ).first()
        assert email_report is not None
        assert email_report.status == "failed"

