"""
Tests for tutor service.
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from app.services.tutor_service import get_tutors, get_tutor_by_id, get_tutor_statistics, get_tutor_history
from app.models.tutor import Tutor
from app.models.tutor_score import TutorScore
from app.models.session import Session as SessionModel
from app.models.reschedule import Reschedule


def test_get_tutors_all(db_session, sample_tutor, sample_tutor_score):
    """Test getting all tutors."""
    # Use a large limit to ensure we get all tutors (including the sample)
    tutors, total = get_tutors(db_session, risk_status="all", limit=1000)
    
    assert total >= 1
    assert len(tutors) >= 1
    assert any(t.id == sample_tutor.id for t in tutors), f"Sample tutor {sample_tutor.id} not found in {len(tutors)} tutors. Total: {total}"


def test_get_tutors_high_risk_filter(db_session, sample_tutor):
    """Test filtering by high risk."""
    # Create high-risk tutor
    high_risk_tutor = Tutor(name="High Risk", is_active=True)
    db_session.add(high_risk_tutor)
    db_session.flush()
    
    high_risk_score = TutorScore(
        tutor_id=high_risk_tutor.id,
        reschedule_rate_30d=Decimal("20.00"),
        is_high_risk=True,
        total_sessions_30d=10,
        tutor_reschedules_30d=2,
        last_calculated_at=datetime.utcnow()
    )
    db_session.add(high_risk_score)
    db_session.commit()
    
    tutors, total = get_tutors(db_session, risk_status="high_risk")
    assert total >= 1
    assert all(t.tutor_score.is_high_risk is True for t in tutors if t.tutor_score)


def test_get_tutors_sorting(db_session, sample_tutor, sample_tutor_score):
    """Test sorting tutors."""
    tutors, _ = get_tutors(db_session, sort_by="name", sort_order="asc")
    
    if len(tutors) > 1:
        names = [t.name for t in tutors]
        assert names == sorted(names)


def test_get_tutors_pagination(db_session, sample_tutor, sample_tutor_score):
    """Test pagination."""
    tutors, total = get_tutors(db_session, limit=1, offset=0)
    
    assert len(tutors) <= 1
    assert total >= 1


def test_get_tutor_by_id_success(db_session, sample_tutor, sample_tutor_score):
    """Test getting tutor by ID."""
    tutor = get_tutor_by_id(str(sample_tutor.id), db_session)
    
    assert tutor is not None
    assert tutor.id == sample_tutor.id
    assert tutor.tutor_score is not None


def test_get_tutor_by_id_not_found(db_session):
    """Test getting non-existent tutor."""
    from uuid import uuid4
    fake_id = uuid4()
    
    tutor = get_tutor_by_id(str(fake_id), db_session)
    assert tutor is None


def test_get_tutor_statistics(db_session, sample_tutor, sample_tutor_score):
    """Test getting tutor statistics."""
    stats = get_tutor_statistics(str(sample_tutor.id), db_session)
    
    assert stats is not None
    assert "reschedule_rate_30d" in stats
    assert "is_high_risk" in stats


def test_get_tutor_history(db_session, sample_tutor, sample_session):
    """Test getting tutor history."""
    # Create reschedule
    reschedule = Reschedule(
        session_id=sample_session.id,
        initiator="tutor",
        original_time=sample_session.scheduled_time,
        new_time=sample_session.scheduled_time + timedelta(days=1),
        reason="Test",
        cancelled_at=sample_session.scheduled_time - timedelta(hours=12),
        hours_before_session=Decimal("12.00")
    )
    db_session.add(reschedule)
    db_session.commit()
    
    reschedules, trend = get_tutor_history(str(sample_tutor.id), days=90, limit=100, db=db_session)
    
    assert len(reschedules) >= 1
    assert "reschedule_rate_by_week" in trend

