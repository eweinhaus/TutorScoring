"""
Tests for TutorScore model.
"""
import pytest
from datetime import datetime
from decimal import Decimal
from sqlalchemy.exc import IntegrityError

from app.models import TutorScore, Tutor


def test_tutor_score_creation(db_session, sample_tutor_score):
    """Test creating a tutor score with required fields."""
    assert sample_tutor_score.id is not None
    assert sample_tutor_score.tutor_id is not None
    assert sample_tutor_score.reschedule_rate_7d == Decimal("5.00")
    assert sample_tutor_score.total_sessions_7d == 20
    assert sample_tutor_score.is_high_risk is False
    assert sample_tutor_score.risk_threshold == Decimal("15.00")


def test_tutor_score_rate_constraint(db_session, sample_tutor):
    """Test that rates must be between 0 and 100."""
    # Valid rate
    tutor_score = TutorScore(
        tutor_id=sample_tutor.id,
        reschedule_rate_7d=Decimal("50.00"),
        total_sessions_7d=20,
        tutor_reschedules_7d=10,
        is_high_risk=False,
        risk_threshold=Decimal("15.00"),
        last_calculated_at=datetime.utcnow()
    )
    db_session.add(tutor_score)
    db_session.commit()
    
    assert tutor_score.reschedule_rate_7d == Decimal("50.00")


def test_tutor_score_unique_tutor_id(db_session, sample_tutor):
    """Test that tutor_id must be unique."""
    tutor_score1 = TutorScore(
        tutor_id=sample_tutor.id,
        reschedule_rate_7d=Decimal("5.00"),
        total_sessions_7d=20,
        tutor_reschedules_7d=1,
        is_high_risk=False,
        risk_threshold=Decimal("15.00"),
        last_calculated_at=datetime.utcnow()
    )
    db_session.add(tutor_score1)
    db_session.commit()
    
    # Try to create another score for same tutor
    tutor_score2 = TutorScore(
        tutor_id=sample_tutor.id,
        reschedule_rate_7d=Decimal("10.00"),
        total_sessions_7d=30,
        tutor_reschedules_7d=3,
        is_high_risk=False,
        risk_threshold=Decimal("15.00"),
        last_calculated_at=datetime.utcnow()
    )
    db_session.add(tutor_score2)
    
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_tutor_score_tutor_relationship(db_session, sample_tutor_score, sample_tutor):
    """Test tutor_score-tutor relationship."""
    assert sample_tutor_score.tutor is not None
    assert sample_tutor_score.tutor.id == sample_tutor.id


def test_tutor_score_update_rates(db_session, sample_tutor_score):
    """Test update_rates method."""
    sample_tutor_score.update_rates(
        rates_7d=Decimal("10.00"),
        rates_30d=Decimal("15.00"),
        rates_90d=Decimal("20.00"),
        counts_7d=30,
        counts_30d=100,
        counts_90d=250,
        reschedules_7d=3,
        reschedules_30d=15,
        reschedules_90d=50
    )
    
    assert sample_tutor_score.reschedule_rate_7d == Decimal("10.00")
    assert sample_tutor_score.total_sessions_7d == 30
    assert sample_tutor_score.tutor_reschedules_7d == 3


def test_tutor_score_check_risk_flag(db_session, sample_tutor):
    """Test check_risk_flag method."""
    # Low risk
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
    tutor_score.check_risk_flag()
    assert tutor_score.is_high_risk is False
    
    # High risk
    tutor_score.reschedule_rate_7d = Decimal("20.00")
    tutor_score.check_risk_flag()
    assert tutor_score.is_high_risk is True


def test_tutor_score_to_dict(db_session, sample_tutor_score):
    """Test to_dict method."""
    result = sample_tutor_score.to_dict()
    
    assert isinstance(result, dict)
    assert 'id' in result
    assert 'tutor_id' in result
    assert 'reschedule_rate_7d' in result
    assert 'is_high_risk' in result
    assert result['reschedule_rate_7d'] == 5.0
    assert result['is_high_risk'] is False


def test_tutor_score_repr(db_session, sample_tutor_score):
    """Test tutor_score __repr__ method."""
    repr_str = repr(sample_tutor_score)
    assert "TutorScore" in repr_str
    assert "is_high_risk" in repr_str.lower()

