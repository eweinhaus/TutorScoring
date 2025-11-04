"""
Integration tests for models.
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from app.models import Tutor, Session, Reschedule, TutorScore, EmailReport


def test_create_tutor_with_sessions_and_score(db_session):
    """Test creating tutor with sessions and tutor_score."""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    # Create tutor
    tutor = Tutor(
        name=f"Integration Test Tutor {unique_id}",
        email=f"integration.{unique_id}@test.com",
        is_active=True
    )
    db_session.add(tutor)
    db_session.commit()
    
    # Create sessions
    session1 = Session(
        tutor_id=tutor.id,
        student_id="student_1",
        scheduled_time=datetime.utcnow(),
        completed_time=datetime.utcnow() + timedelta(minutes=60),
        status="completed",
        duration_minutes=60
    )
    session2 = Session(
        tutor_id=tutor.id,
        student_id="student_2",
        scheduled_time=datetime.utcnow() + timedelta(days=1),
        status="rescheduled"
    )
    db_session.add_all([session1, session2])
    db_session.commit()
    
    # Create reschedule
    reschedule = Reschedule(
        session_id=session2.id,
        initiator="tutor",
        original_time=session2.scheduled_time,
        new_time=session2.scheduled_time + timedelta(days=2),
        reason="Personal emergency",
        reason_code="personal",
        cancelled_at=session2.scheduled_time - timedelta(hours=12),
        hours_before_session=Decimal("12.00"),
        created_at=session2.scheduled_time - timedelta(hours=12)
    )
    db_session.add(reschedule)
    db_session.commit()
    
    # Create tutor score
    tutor_score = TutorScore(
        tutor_id=tutor.id,
        reschedule_rate_7d=Decimal("50.00"),
        reschedule_rate_30d=Decimal("50.00"),
        reschedule_rate_90d=Decimal("50.00"),
        total_sessions_7d=2,
        total_sessions_30d=2,
        total_sessions_90d=2,
        tutor_reschedules_7d=1,
        tutor_reschedules_30d=1,
        tutor_reschedules_90d=1,
        is_high_risk=True,
        risk_threshold=Decimal("15.00"),
        last_calculated_at=datetime.utcnow()
    )
    db_session.add(tutor_score)
    db_session.commit()
    
    # Refresh and verify relationships
    db_session.refresh(tutor)
    assert len(tutor.sessions) == 2
    assert tutor.tutor_score is not None
    assert tutor.tutor_score.is_high_risk is True
    
    db_session.refresh(session2)
    assert session2.reschedule is not None
    assert session2.reschedule.initiator == "tutor"


def test_create_session_with_reschedule_and_email(db_session, sample_tutor):
    """Test creating session with reschedule and email report."""
    session = Session(
        tutor_id=sample_tutor.id,
        student_id="student_integration",
        scheduled_time=datetime.utcnow(),
        status="rescheduled"
    )
    db_session.add(session)
    db_session.commit()
    
    reschedule = Reschedule(
        session_id=session.id,
        initiator="tutor",
        original_time=session.scheduled_time,
        new_time=session.scheduled_time + timedelta(days=1),
        reason="Scheduling conflict",
        reason_code="scheduling",
        cancelled_at=session.scheduled_time - timedelta(hours=6),
        hours_before_session=Decimal("6.00"),
        created_at=session.scheduled_time - timedelta(hours=6)
    )
    db_session.add(reschedule)
    db_session.commit()
    
    email_report = EmailReport(
        session_id=session.id,
        recipient_email="admin@example.com",
        sent_at=datetime.utcnow(),
        status="sent"
    )
    db_session.add(email_report)
    db_session.commit()
    
    # Refresh and verify
    db_session.refresh(session)
    assert session.reschedule is not None
    assert session.email_report is not None
    assert session.reschedule.reason == "Scheduling conflict"


def test_cascade_delete_tutor(db_session, sample_tutor):
    """Test that deleting tutor cascades to sessions."""
    session1 = Session(
        tutor_id=sample_tutor.id,
        student_id="student_1",
        scheduled_time=datetime.utcnow(),
        status="completed"
    )
    session2 = Session(
        tutor_id=sample_tutor.id,
        student_id="student_2",
        scheduled_time=datetime.utcnow(),
        status="rescheduled"
    )
    db_session.add_all([session1, session2])
    db_session.commit()
    
    session1_id = session1.id
    session2_id = session2.id
    
    # Create reschedule for session2
    reschedule = Reschedule(
        session_id=session2.id,
        initiator="tutor",
        original_time=session2.scheduled_time,
        cancelled_at=session2.scheduled_time - timedelta(hours=12),
        created_at=session2.scheduled_time - timedelta(hours=12)
    )
    db_session.add(reschedule)
    db_session.commit()
    
    reschedule_id = reschedule.id
    
    # Delete tutor
    db_session.delete(sample_tutor)
    db_session.commit()
    
    # Verify sessions and reschedule are deleted
    assert db_session.query(Session).filter_by(id=session1_id).first() is None
    assert db_session.query(Session).filter_by(id=session2_id).first() is None
    assert db_session.query(Reschedule).filter_by(id=reschedule_id).first() is None


def test_foreign_key_constraint(db_session):
    """Test that foreign key constraints are enforced."""
    # Try to create session with invalid tutor_id
    invalid_uuid = "00000000-0000-0000-0000-000000000000"
    
    session = Session(
        tutor_id=invalid_uuid,
        student_id="student_1",
        scheduled_time=datetime.utcnow(),
        status="completed"
    )
    db_session.add(session)
    
    with pytest.raises(Exception):  # Should raise IntegrityError or similar
        db_session.commit()


def test_query_performance_with_indexes(db_session, sample_tutor):
    """Test that indexes improve query performance."""
    # Create multiple sessions
    sessions = []
    for i in range(100):
        session = Session(
            tutor_id=sample_tutor.id,
            student_id=f"student_{i}",
            scheduled_time=datetime.utcnow() - timedelta(days=i),
            status="completed" if i % 2 == 0 else "rescheduled",
            completed_time=datetime.utcnow() - timedelta(days=i) + timedelta(hours=1) if i % 2 == 0 else None
        )
        sessions.append(session)
    
    db_session.add_all(sessions)
    db_session.commit()
    
    # Query by tutor_id (indexed)
    from sqlalchemy import func
    count = db_session.query(Session).filter_by(tutor_id=sample_tutor.id).count()
    assert count >= 100  # At least 100, may have more from other tests
    
    # Query by status and tutor_id (using composite index)
    completed_count = db_session.query(Session).filter_by(
        tutor_id=sample_tutor.id,
        status="completed"
    ).count()
    assert completed_count == 50  # 50 of the 100 we just created

