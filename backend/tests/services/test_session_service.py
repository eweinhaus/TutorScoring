"""
Tests for session service.
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.services.session_service import create_session
from app.schemas.session import SessionCreate
from app.schemas.reschedule import RescheduleInfo
from app.models.session import Session as SessionModel
from app.models.tutor import Tutor
from app.models.reschedule import Reschedule


def test_create_session_success(db_session, sample_tutor):
    """Test successful session creation."""
    session_id = uuid4()
    session_data = SessionCreate(
        session_id=session_id,
        tutor_id=sample_tutor.id,
        student_id="student_123",
        scheduled_time=datetime.utcnow(),
        completed_time=datetime.utcnow() + timedelta(hours=1),
        status="completed",
        duration_minutes=60
    )
    
    session = create_session(session_data, db_session)
    
    assert session.id == session_id
    assert session.tutor_id == sample_tutor.id
    assert session.status == "completed"


def test_create_session_with_reschedule(db_session, sample_tutor):
    """Test session creation with reschedule."""
    session_id = uuid4()
    original_time = datetime.utcnow()
    new_time = original_time + timedelta(days=1)
    
    reschedule_info = RescheduleInfo(
        initiator="tutor",
        original_time=original_time,
        new_time=new_time,
        reason="Personal emergency",
        cancelled_at=original_time - timedelta(hours=12)
    )
    
    session_data = SessionCreate(
        session_id=session_id,
        tutor_id=sample_tutor.id,
        student_id="student_123",
        scheduled_time=original_time,
        status="rescheduled",
        reschedule_info=reschedule_info
    )
    
    session = create_session(session_data, db_session)
    
    assert session.status == "rescheduled"
    assert session.reschedule is not None
    assert session.reschedule.initiator == "tutor"


def test_create_session_creates_tutor_if_not_exists(db_session):
    """Test that tutor is created if it doesn't exist."""
    tutor_id = uuid4()
    session_id = uuid4()
    
    session_data = SessionCreate(
        session_id=session_id,
        tutor_id=tutor_id,
        student_id="student_123",
        scheduled_time=datetime.utcnow(),
        status="completed"
    )
    
    session = create_session(session_data, db_session)
    
    # Verify tutor was created
    tutor = db_session.query(Tutor).filter(Tutor.id == tutor_id).first()
    assert tutor is not None


def test_create_session_duplicate_id(db_session, sample_tutor):
    """Test that duplicate session_id raises error."""
    session_id = uuid4()
    
    session_data = SessionCreate(
        session_id=session_id,
        tutor_id=sample_tutor.id,
        student_id="student_123",
        scheduled_time=datetime.utcnow(),
        status="completed"
    )
    
    # Create first session
    create_session(session_data, db_session)
    
    # Try to create duplicate
    with pytest.raises(ValueError, match="already exists"):
        create_session(session_data, db_session)

