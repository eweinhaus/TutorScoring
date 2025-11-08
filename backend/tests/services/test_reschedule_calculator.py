"""
Tests for reschedule rate calculator service.
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from app.services.reschedule_calculator import calculate_reschedule_rate, get_session_counts
from app.models.tutor import Tutor
from app.models.session import Session as SessionModel
from app.models.reschedule import Reschedule


def test_calculate_reschedule_rate_no_sessions(db_session, sample_tutor):
    """Test calculation with no sessions returns 0.0."""
    rate = calculate_reschedule_rate(str(sample_tutor.id), 30, db_session)
    assert rate == 0.0


def test_calculate_reschedule_rate_no_reschedules(db_session, sample_tutor):
    """Test calculation with sessions but no reschedules."""
    # Create completed sessions
    for i in range(10):
        session = SessionModel(
            tutor_id=sample_tutor.id,
            student_id=f"student_{i}",
            scheduled_time=datetime.utcnow() - timedelta(days=i),
            completed_time=datetime.utcnow() - timedelta(days=i) + timedelta(hours=1),
            status="completed",
            duration_minutes=60
        )
        db_session.add(session)
    db_session.commit()
    
    rate = calculate_reschedule_rate(str(sample_tutor.id), 30, db_session)
    assert rate == 0.0


def test_calculate_reschedule_rate_with_reschedules(db_session, sample_tutor):
    """Test calculation with tutor-initiated reschedules."""
    # Create 10 sessions
    sessions = []
    for i in range(10):
        session = SessionModel(
            tutor_id=sample_tutor.id,
            student_id=f"student_{i}",
            scheduled_time=datetime.utcnow() - timedelta(days=i),
            status="rescheduled",
            duration_minutes=None
        )
        db_session.add(session)
        sessions.append(session)
    db_session.flush()
    
    # Create 3 tutor-initiated reschedules
    for i in range(3):
        reschedule = Reschedule(
            session_id=sessions[i].id,
            initiator="tutor",
            original_time=sessions[i].scheduled_time,
            new_time=sessions[i].scheduled_time + timedelta(days=1),
            reason="Test",
            cancelled_at=sessions[i].scheduled_time - timedelta(hours=12),
            hours_before_session=Decimal("12.00")
        )
        db_session.add(reschedule)
    db_session.commit()
    
    rate = calculate_reschedule_rate(str(sample_tutor.id), 30, db_session)
    assert rate == 30.0  # 3 reschedules / 10 sessions = 30%


def test_calculate_reschedule_rate_student_reschedules_not_counted(db_session, sample_tutor):
    """Test that student-initiated reschedules are not counted."""
    # Create session with student-initiated reschedule
    session = SessionModel(
        tutor_id=sample_tutor.id,
        student_id="student_1",
        scheduled_time=datetime.utcnow(),
        status="rescheduled"
    )
    db_session.add(session)
    db_session.flush()
    
    reschedule = Reschedule(
        session_id=session.id,
        initiator="student",  # Student-initiated
        original_time=session.scheduled_time,
        new_time=session.scheduled_time + timedelta(days=1),
        reason="Test",
        cancelled_at=session.scheduled_time - timedelta(hours=12),
        hours_before_session=Decimal("12.00")
    )
    db_session.add(reschedule)
    db_session.commit()
    
    rate = calculate_reschedule_rate(str(sample_tutor.id), 30, db_session)
    assert rate == 0.0  # Student reschedules don't count


def test_get_session_counts(db_session, sample_tutor):
    """Test getting session counts."""
    # Create sessions
    for i in range(5):
        session = SessionModel(
            tutor_id=sample_tutor.id,
            student_id=f"student_{i}",
            scheduled_time=datetime.utcnow() - timedelta(days=i),
            status="completed" if i < 3 else "rescheduled",
            completed_time=datetime.utcnow() - timedelta(days=i) + timedelta(hours=1) if i < 3 else None,
            duration_minutes=60 if i < 3 else None
        )
        db_session.add(session)
    db_session.commit()
    
    total, reschedules = get_session_counts(str(sample_tutor.id), 30, db_session)
    assert total == 5
    assert reschedules == 0  # No tutor-initiated reschedules yet

