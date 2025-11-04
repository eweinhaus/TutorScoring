"""
Tests for tutor query endpoints.
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from decimal import Decimal

from app.main import app
from app.models.tutor import Tutor
from app.models.tutor_score import TutorScore

@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


def test_get_tutors_success(client, db_session, sample_tutor, sample_tutor_score):
    """Test getting tutor list."""
    response = client.get("/api/tutors")
    
    assert response.status_code == 200
    data = response.json()
    assert "tutors" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert len(data["tutors"]) > 0


def test_get_tutors_with_risk_filter(client, db_session, sample_tutor, sample_tutor_score):
    """Test filtering tutors by risk status."""
    # Create high-risk tutor
    high_risk_tutor = Tutor(
        name="High Risk Tutor",
        is_active=True
    )
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
    
    # Test high_risk filter
    response = client.get("/api/tutors?risk_status=high_risk")
    assert response.status_code == 200
    data = response.json()
    assert all(t["is_high_risk"] is True for t in data["tutors"])


def test_get_tutors_with_sorting(client, db_session, sample_tutor, sample_tutor_score):
    """Test sorting tutors."""
    response = client.get("/api/tutors?sort_by=name&sort_order=asc")
    assert response.status_code == 200
    data = response.json()
    
    if len(data["tutors"]) > 1:
        names = [t["name"] for t in data["tutors"]]
        assert names == sorted(names)


def test_get_tutors_pagination(client, db_session, sample_tutor, sample_tutor_score):
    """Test pagination."""
    response = client.get("/api/tutors?limit=1&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert len(data["tutors"]) <= 1
    assert data["limit"] == 1
    assert data["offset"] == 0


def test_get_tutor_detail_success(client, db_session, sample_tutor, sample_tutor_score):
    """Test getting tutor detail."""
    response = client.get(f"/api/tutors/{sample_tutor.id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(sample_tutor.id)
    assert data["name"] == sample_tutor.name
    assert "scores" in data
    assert "statistics" in data


def test_get_tutor_detail_not_found(client, db_session):
    """Test getting non-existent tutor."""
    from uuid import uuid4
    fake_id = uuid4()
    
    response = client.get(f"/api/tutors/{fake_id}")
    assert response.status_code == 404


def test_get_tutor_detail_invalid_uuid(client, db_session):
    """Test getting tutor with invalid UUID."""
    response = client.get("/api/tutors/not-a-uuid")
    assert response.status_code == 400


def test_get_tutor_history_success(client, db_session, sample_tutor, sample_session):
    """Test getting tutor history."""
    from app.models.reschedule import Reschedule
    from datetime import datetime, timedelta
    
    # Create reschedule
    reschedule = Reschedule(
        session_id=sample_session.id,
        initiator="tutor",
        original_time=sample_session.scheduled_time,
        new_time=sample_session.scheduled_time + timedelta(days=1),
        reason="Test reason",
        cancelled_at=sample_session.scheduled_time - timedelta(hours=12),
        hours_before_session=Decimal("12.00")
    )
    db_session.add(reschedule)
    db_session.commit()
    
    response = client.get(f"/api/tutors/{sample_tutor.id}/history")
    assert response.status_code == 200
    data = response.json()
    assert "reschedules" in data
    assert "trend" in data


def test_get_tutors_invalid_filter(client, db_session):
    """Test invalid filter parameter."""
    response = client.get("/api/tutors?risk_status=invalid")
    assert response.status_code == 400


def test_get_tutors_invalid_sort(client, db_session):
    """Test invalid sort parameter."""
    response = client.get("/api/tutors?sort_by=invalid_field")
    assert response.status_code == 400

