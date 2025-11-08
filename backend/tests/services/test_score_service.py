"""
Tests for score update service.
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from app.services.score_service import update_scores_for_tutor, check_risk_flag
from app.models.tutor import Tutor
from app.models.tutor_score import TutorScore
from app.models.session import Session as SessionModel
from app.models.reschedule import Reschedule


def test_update_scores_for_tutor_creates_record(db_session, sample_tutor):
    """Test that score record is created if it doesn't exist."""
    score = update_scores_for_tutor(str(sample_tutor.id), db_session)
    
    assert score is not None
    assert score.tutor_id == sample_tutor.id
    assert score.last_calculated_at is not None


def test_update_scores_for_tutor_updates_existing(db_session, sample_tutor):
    """Test that existing score record is updated."""
    # Create initial score
    initial_score = TutorScore(
        tutor_id=sample_tutor.id,
        reschedule_rate_30d=Decimal("10.00"),
        is_high_risk=False,
        total_sessions_30d=10,
        tutor_reschedules_30d=1,
        last_calculated_at=datetime.utcnow() - timedelta(hours=2)
    )
    db_session.add(initial_score)
    db_session.commit()
    
    # Update scores
    updated_score = update_scores_for_tutor(str(sample_tutor.id), db_session)
    
    assert updated_score.id == initial_score.id
    assert updated_score.last_calculated_at >= initial_score.last_calculated_at


def test_update_scores_for_tutor_high_risk_flag(db_session, sample_tutor):
    """Test that high risk flag is set when rate exceeds threshold."""
    # Create sessions with high reschedule rate
    sessions = []
    for i in range(10):
        session = SessionModel(
            tutor_id=sample_tutor.id,
            student_id=f"student_{i}",
            scheduled_time=datetime.utcnow() - timedelta(days=i),
            status="rescheduled" if i < 2 else "completed",
            completed_time=None if i < 2 else datetime.utcnow() - timedelta(days=i) + timedelta(hours=1),
            duration_minutes=None if i < 2 else 60
        )
        db_session.add(session)
        sessions.append(session)
    db_session.flush()
    
    # Create 2 tutor-initiated reschedules (20% rate)
    for i in range(2):
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
    
    # Update scores (threshold is 15%, rate is 20%)
    score = update_scores_for_tutor(str(sample_tutor.id), db_session, risk_threshold=15.0)
    
    assert score.is_high_risk is True


def test_update_scores_for_tutor_low_risk_flag(db_session, sample_tutor):
    """Test that high risk flag is not set when rate is below threshold."""
    # Create sessions with low reschedule rate
    sessions = []
    for i in range(10):
        session = SessionModel(
            tutor_id=sample_tutor.id,
            student_id=f"student_{i}",
            scheduled_time=datetime.utcnow() - timedelta(days=i),
            status="completed",
            completed_time=datetime.utcnow() - timedelta(days=i) + timedelta(hours=1),
            duration_minutes=60
        )
        db_session.add(session)
        sessions.append(session)
    db_session.commit()
    
    # Update scores (no reschedules, rate is 0%)
    score = update_scores_for_tutor(str(sample_tutor.id), db_session, risk_threshold=15.0)
    
    assert score.is_high_risk is False


def test_update_scores_for_tutor_invalid_tutor_id(db_session):
    """Test that ValueError is raised for invalid tutor_id."""
    from uuid import uuid4
    fake_id = uuid4()
    
    with pytest.raises(ValueError, match="Tutor with id.*not found"):
        update_scores_for_tutor(str(fake_id), db_session)


def test_check_risk_flag(db_session, sample_tutor):
    """Test risk flag checking."""
    # Create score with high rate
    score = TutorScore(
        tutor_id=sample_tutor.id,
        reschedule_rate_30d=Decimal("20.00"),
        is_high_risk=False,  # Initially false
        total_sessions_30d=10,
        tutor_reschedules_30d=2,
        risk_threshold=Decimal("15.00"),
        last_calculated_at=datetime.utcnow()
    )
    db_session.add(score)
    db_session.commit()
    
    # Check risk flag
    is_high_risk = check_risk_flag(str(sample_tutor.id), 15.0, db_session)
    
    assert is_high_risk is True
    db_session.refresh(score)
    assert score.is_high_risk is True

