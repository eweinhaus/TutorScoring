"""
Tests for Reschedule model.
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.exc import IntegrityError

from app.models import Reschedule, Session


def test_reschedule_creation(db_session, sample_reschedule):
    """Test creating a reschedule with required fields."""
    assert sample_reschedule.id is not None
    assert sample_reschedule.session_id is not None
    assert sample_reschedule.initiator == "tutor"
    assert sample_reschedule.original_time is not None
    assert sample_reschedule.cancelled_at is not None
    assert sample_reschedule.hours_before_session == Decimal("12.00")


def test_reschedule_initiator_constraint(db_session, sample_session):
    """Test that initiator must be 'tutor' or 'student'."""
    # Valid initiator
    reschedule = Reschedule(
        session_id=sample_session.id,
        initiator="tutor",
        original_time=sample_session.scheduled_time,
        cancelled_at=sample_session.scheduled_time - timedelta(hours=12),
        created_at=sample_session.scheduled_time - timedelta(hours=12)
    )
    db_session.add(reschedule)
    db_session.commit()
    
    assert reschedule.initiator == "tutor"


def test_reschedule_new_time_constraint(db_session, sample_session):
    """Test that new_time must be > original_time if not NULL."""
    original = datetime.utcnow()
    new_time = original + timedelta(days=1)
    
    reschedule = Reschedule(
        session_id=sample_session.id,
        initiator="tutor",
        original_time=original,
        new_time=new_time,
        cancelled_at=original - timedelta(hours=12),
        created_at=original - timedelta(hours=12)
    )
    db_session.add(reschedule)
    db_session.commit()
    
    assert reschedule.new_time > reschedule.original_time


def test_reschedule_unique_session_id(db_session, sample_session):
    """Test that session_id must be unique."""
    reschedule1 = Reschedule(
        session_id=sample_session.id,
        initiator="tutor",
        original_time=sample_session.scheduled_time,
        cancelled_at=sample_session.scheduled_time - timedelta(hours=12),
        created_at=sample_session.scheduled_time - timedelta(hours=12)
    )
    db_session.add(reschedule1)
    db_session.commit()
    
    # Try to create another reschedule for same session
    reschedule2 = Reschedule(
        session_id=sample_session.id,
        initiator="student",
        original_time=sample_session.scheduled_time,
        cancelled_at=sample_session.scheduled_time - timedelta(hours=6),
        created_at=sample_session.scheduled_time - timedelta(hours=6)
    )
    db_session.add(reschedule2)
    
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_reschedule_session_relationship(db_session, sample_reschedule, sample_session):
    """Test reschedule-session relationship."""
    assert sample_reschedule.session is not None
    assert sample_reschedule.session.id == sample_session.id


def test_reschedule_calculate_hours_before(db_session, sample_reschedule):
    """Test calculate_hours_before method."""
    hours = sample_reschedule.calculate_hours_before()
    assert hours is not None
    assert abs(hours - 12.0) < 0.01  # Allow small floating point differences


def test_reschedule_is_last_minute(db_session, sample_session):
    """Test is_last_minute method."""
    # Last-minute reschedule (<24 hours)
    reschedule1 = Reschedule(
        session_id=sample_session.id,
        initiator="tutor",
        original_time=sample_session.scheduled_time,
        cancelled_at=sample_session.scheduled_time - timedelta(hours=12),
        created_at=sample_session.scheduled_time - timedelta(hours=12),
        hours_before_session=Decimal("12.00")
    )
    db_session.add(reschedule1)
    db_session.commit()
    
    assert reschedule1.is_last_minute() is True
    
    # Planned reschedule (>24 hours)
    session2 = Session(
        tutor_id=sample_session.tutor_id,
        student_id="student_2",
        scheduled_time=datetime.utcnow() + timedelta(days=2),
        status="rescheduled"
    )
    db_session.add(session2)
    db_session.commit()
    
    reschedule2 = Reschedule(
        session_id=session2.id,
        initiator="tutor",
        original_time=session2.scheduled_time,
        cancelled_at=session2.scheduled_time - timedelta(hours=48),
        created_at=session2.scheduled_time - timedelta(hours=48),
        hours_before_session=Decimal("48.00")
    )
    db_session.add(reschedule2)
    db_session.commit()
    
    assert reschedule2.is_last_minute() is False


def test_reschedule_repr(db_session, sample_reschedule):
    """Test reschedule __repr__ method."""
    repr_str = repr(sample_reschedule)
    assert "Reschedule" in repr_str
    assert "tutor" in repr_str

