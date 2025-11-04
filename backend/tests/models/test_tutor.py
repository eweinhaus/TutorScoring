"""
Tests for Tutor model.
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.exc import IntegrityError

from app.models import Tutor, Session, TutorScore


def test_tutor_creation(db_session, sample_tutor):
    """Test creating a tutor with required fields."""
    assert sample_tutor.id is not None
    assert sample_tutor.name.startswith("John Doe")
    assert "john.doe" in sample_tutor.email
    assert sample_tutor.is_active is True
    assert sample_tutor.created_at is not None
    assert sample_tutor.updated_at is not None


def test_tutor_creation_optional_email(db_session):
    """Test creating a tutor without email."""
    tutor = Tutor(
        name="Jane Doe",
        email=None,
        is_active=True
    )
    db_session.add(tutor)
    db_session.commit()
    
    assert tutor.email is None
    assert tutor.name == "Jane Doe"


def test_tutor_unique_email(db_session):
    """Test that email must be unique."""
    import uuid
    unique_email = f"test_{uuid.uuid4()}@example.com"
    tutor1 = Tutor(name="Tutor 1", email=unique_email)
    db_session.add(tutor1)
    db_session.commit()
    
    tutor2 = Tutor(name="Tutor 2", email=unique_email)
    db_session.add(tutor2)
    
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_tutor_sessions_relationship(db_session, sample_tutor):
    """Test tutor-sessions relationship."""
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
        status="completed"
    )
    db_session.add_all([session1, session2])
    db_session.commit()
    
    db_session.refresh(sample_tutor)
    assert len(sample_tutor.sessions) == 2
    assert session1 in sample_tutor.sessions
    assert session2 in sample_tutor.sessions


def test_tutor_tutor_score_relationship(db_session, sample_tutor):
    """Test tutor-tutor_score relationship."""
    tutor_score = TutorScore(
        tutor_id=sample_tutor.id,
        reschedule_rate_7d=5.0,
        total_sessions_7d=20,
        tutor_reschedules_7d=1,
        is_high_risk=False,
        risk_threshold=15.0,
        last_calculated_at=datetime.utcnow()
    )
    db_session.add(tutor_score)
    db_session.commit()
    
    db_session.refresh(sample_tutor)
    assert sample_tutor.tutor_score is not None
    assert sample_tutor.tutor_score.tutor_id == sample_tutor.id


def test_tutor_get_reschedule_rate(db_session, sample_tutor):
    """Test get_reschedule_rate method."""
    # Create some sessions
    now = datetime.utcnow()
    cutoff = now - timedelta(days=7)
    
    import uuid
    student_id1 = f"student_{uuid.uuid4()}"
    student_id2 = f"student_{uuid.uuid4()}"
    
    # Completed session
    session1 = Session(
        tutor_id=sample_tutor.id,
        student_id=student_id1,
        scheduled_time=cutoff + timedelta(days=1),
        status="completed",
        completed_time=cutoff + timedelta(days=1, hours=1)
    )
    db_session.add(session1)
    db_session.commit()
    
    # Rescheduled session (tutor-initiated)
    session2 = Session(
        tutor_id=sample_tutor.id,
        student_id=student_id2,
        scheduled_time=cutoff + timedelta(days=2),
        status="rescheduled"
    )
    db_session.add(session2)
    db_session.commit()
    
    from app.models import Reschedule
    reschedule = Reschedule(
        session_id=session2.id,
        initiator="tutor",
        original_time=session2.scheduled_time,
        cancelled_at=session2.scheduled_time - timedelta(hours=12),
        created_at=session2.scheduled_time - timedelta(hours=12)
    )
    db_session.add(reschedule)
    db_session.commit()
    
    # Refresh tutor to load relationships
    db_session.refresh(sample_tutor)
    
    rate = sample_tutor.get_reschedule_rate(7)
    assert rate is not None
    assert rate == 50.0  # 1 reschedule out of 2 sessions


def test_tutor_calculate_risk_score(db_session, sample_tutor):
    """Test calculate_risk_score method."""
    tutor_score = TutorScore(
        tutor_id=sample_tutor.id,
        reschedule_rate_7d=Decimal("5.00"),
        reschedule_rate_30d=Decimal("8.00"),
        reschedule_rate_90d=Decimal("10.00"),
        total_sessions_7d=20,
        total_sessions_30d=80,
        total_sessions_90d=200,
        tutor_reschedules_7d=1,
        tutor_reschedules_30d=6,
        tutor_reschedules_90d=20,
        is_high_risk=False,
        risk_threshold=Decimal("15.00"),
        last_calculated_at=datetime.utcnow()
    )
    db_session.add(tutor_score)
    db_session.commit()
    
    db_session.refresh(sample_tutor)
    risk = sample_tutor.calculate_risk_score()
    assert risk == "medium"  # Max rate is 10%, which is medium (>= 10% and < 20%)


def test_tutor_calculate_risk_score_high(db_session, sample_tutor):
    """Test calculate_risk_score with high risk."""
    tutor_score = TutorScore(
        tutor_id=sample_tutor.id,
        reschedule_rate_7d=25.0,
        reschedule_rate_30d=22.0,
        reschedule_rate_90d=20.0,
        total_sessions_7d=20,
        total_sessions_30d=80,
        total_sessions_90d=200,
        tutor_reschedules_7d=5,
        tutor_reschedules_30d=18,
        tutor_reschedules_90d=40,
        is_high_risk=True,
        risk_threshold=15.0,
        last_calculated_at=datetime.utcnow()
    )
    db_session.add(tutor_score)
    db_session.commit()
    
    db_session.refresh(sample_tutor)
    risk = sample_tutor.calculate_risk_score()
    assert risk == "high"


def test_tutor_cascade_delete(db_session, sample_tutor):
    """Test that deleting tutor deletes related sessions."""
    session = Session(
        tutor_id=sample_tutor.id,
        student_id="student_1",
        scheduled_time=datetime.utcnow(),
        status="completed"
    )
    db_session.add(session)
    db_session.commit()
    
    session_id = session.id
    
    # Delete tutor
    db_session.delete(sample_tutor)
    db_session.commit()
    
    # Session should be deleted
    deleted_session = db_session.query(Session).filter_by(id=session_id).first()
    assert deleted_session is None


def test_tutor_repr(db_session, sample_tutor):
    """Test tutor __repr__ method."""
    repr_str = repr(sample_tutor)
    assert "Tutor" in repr_str
    assert sample_tutor.name in repr_str

