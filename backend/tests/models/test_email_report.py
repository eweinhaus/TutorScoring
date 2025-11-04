"""
Tests for EmailReport model.
"""
import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from app.models import EmailReport, Session


def test_email_report_creation(db_session, sample_email_report):
    """Test creating an email report with required fields."""
    assert sample_email_report.id is not None
    assert sample_email_report.session_id is not None
    assert sample_email_report.recipient_email == "admin@example.com"
    assert sample_email_report.status == "sent"
    assert sample_email_report.sent_at is not None


def test_email_report_status_constraint(db_session, sample_session):
    """Test that status must be one of allowed values."""
    # Valid status
    email_report = EmailReport(
        session_id=sample_session.id,
        recipient_email="admin@example.com",
        sent_at=datetime.utcnow(),
        status="sent"
    )
    db_session.add(email_report)
    db_session.commit()
    
    assert email_report.status == "sent"


def test_email_report_session_relationship(db_session, sample_email_report, sample_session):
    """Test email_report-session relationship."""
    assert sample_email_report.session is not None
    assert sample_email_report.session.id == sample_session.id


def test_email_report_mark_sent(db_session, sample_session):
    """Test mark_sent method."""
    email_report = EmailReport(
        session_id=sample_session.id,
        recipient_email="admin@example.com",
        sent_at=datetime.utcnow(),
        status="pending"
    )
    db_session.add(email_report)
    db_session.commit()
    
    email_report.mark_sent()
    db_session.commit()
    
    assert email_report.status == "sent"
    assert email_report.error_message is None


def test_email_report_mark_failed(db_session, sample_session):
    """Test mark_failed method."""
    email_report = EmailReport(
        session_id=sample_session.id,
        recipient_email="admin@example.com",
        sent_at=datetime.utcnow(),
        status="pending"
    )
    db_session.add(email_report)
    db_session.commit()
    
    error_msg = "SMTP connection failed"
    email_report.mark_failed(error_msg)
    db_session.commit()
    
    assert email_report.status == "failed"
    assert email_report.error_message == error_msg


def test_email_report_repr(db_session, sample_email_report):
    """Test email_report __repr__ method."""
    repr_str = repr(sample_email_report)
    assert "EmailReport" in repr_str
    assert "sent" in repr_str.lower()

