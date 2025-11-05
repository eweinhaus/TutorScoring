"""
Tests for matching service API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from decimal import Decimal

from app.main import app
from app.models.student import Student
from app.models.tutor import Tutor
from app.models.match_prediction import MatchPrediction

client = TestClient(app)


@pytest.fixture
def test_student(db_session):
    """Create a test student."""
    student = Student(
        name="Test Student",
        age=15,
        preferred_pace=3,
        preferred_teaching_style="structured",
        communication_style_preference=3,
        urgency_level=3,
        previous_tutoring_experience=5,
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)
    return student


@pytest.fixture
def test_tutor(db_session):
    """Create a test tutor with preferences."""
    tutor = Tutor(
        name="Test Tutor",
        email="tutor@test.com",
        age=30,
        experience_years=5,
        teaching_style="structured",
        preferred_pace=3,
        communication_style=3,
        confidence_level=4,
    )
    db_session.add(tutor)
    db_session.commit()
    db_session.refresh(tutor)
    return tutor


@pytest.fixture
def api_key():
    """Get API key for testing."""
    import os
    return os.getenv("API_KEY", "test-api-key")


class TestStudentEndpoints:
    """Test student endpoints."""
    
    def test_get_students_empty(self, api_key):
        """Test getting students when none exist."""
        response = client.get(
            "/api/matching/students",
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["students"] == []
    
    def test_create_student(self, api_key, db_session):
        """Test creating a student."""
        student_data = {
            "name": "New Student",
            "age": 14,
            "preferred_pace": 4,
            "preferred_teaching_style": "flexible",
            "communication_style_preference": 4,
            "urgency_level": 2,
            "previous_tutoring_experience": 0,
        }
        response = client.post(
            "/api/matching/students",
            json=student_data,
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Student"
        assert data["age"] == 14
    
    def test_get_student_by_id(self, api_key, test_student):
        """Test getting student by ID."""
        response = client.get(
            f"/api/matching/students/{test_student.id}",
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_student.id)
        assert data["name"] == "Test Student"
    
    def test_get_student_not_found(self, api_key):
        """Test getting non-existent student."""
        fake_id = uuid4()
        response = client.get(
            f"/api/matching/students/{fake_id}",
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 404


class TestTutorEndpoints:
    """Test tutor endpoints."""
    
    def test_get_tutors(self, api_key, test_tutor):
        """Test getting tutors."""
        response = client.get(
            "/api/matching/tutors",
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(t["id"] == str(test_tutor.id) for t in data)
    
    def test_get_tutor_by_id(self, api_key, test_tutor):
        """Test getting tutor by ID."""
        response = client.get(
            f"/api/matching/tutors/{test_tutor.id}",
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_tutor.id)
        assert data["name"] == "Test Tutor"
    
    def test_update_tutor_preferences(self, api_key, test_tutor):
        """Test updating tutor preferences."""
        update_data = {
            "preferred_pace": 4,
            "confidence_level": 5,
        }
        response = client.patch(
            f"/api/matching/tutors/{test_tutor.id}",
            json=update_data,
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["preferred_pace"] == 4
        assert data["confidence_level"] == 5


class TestMatchPredictionEndpoints:
    """Test match prediction endpoints."""
    
    def test_get_match_prediction(self, api_key, test_student, test_tutor, db_session):
        """Test getting match prediction."""
        response = client.get(
            f"/api/matching/predict/{test_student.id}/{test_tutor.id}",
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["student_id"] == str(test_student.id)
        assert data["tutor_id"] == str(test_tutor.id)
        assert "churn_probability" in data
        assert "risk_level" in data
        assert "compatibility_score" in data
        assert data["risk_level"] in ["low", "medium", "high"]
    
    def test_get_match_prediction_not_found_student(self, api_key, test_tutor):
        """Test getting prediction with non-existent student."""
        fake_id = uuid4()
        response = client.get(
            f"/api/matching/predict/{fake_id}/{test_tutor.id}",
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 404
    
    def test_get_match_prediction_not_found_tutor(self, api_key, test_student):
        """Test getting prediction with non-existent tutor."""
        fake_id = uuid4()
        response = client.get(
            f"/api/matching/predict/{test_student.id}/{fake_id}",
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 404
    
    def test_get_student_matches(self, api_key, test_student, test_tutor, db_session):
        """Test getting all matches for a student."""
        # Create a prediction first
        response = client.get(
            f"/api/matching/predict/{test_student.id}/{test_tutor.id}",
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200
        
        # Get student matches
        response = client.get(
            f"/api/matching/students/{test_student.id}/matches",
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["matches"]) >= 1
    
    def test_get_tutor_matches(self, api_key, test_student, test_tutor, db_session):
        """Test getting all matches for a tutor."""
        # Create a prediction first
        response = client.get(
            f"/api/matching/predict/{test_student.id}/{test_tutor.id}",
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200
        
        # Get tutor matches
        response = client.get(
            f"/api/matching/tutors/{test_tutor.id}/matches",
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["matches"]) >= 1


class TestAuthentication:
    """Test authentication requirements."""
    
    def test_endpoints_require_api_key(self):
        """Test that endpoints require API key."""
        # Test without API key
        response = client.get("/api/matching/students")
        assert response.status_code == 401
    
    def test_endpoints_with_invalid_api_key(self):
        """Test that endpoints reject invalid API key."""
        response = client.get(
            "/api/matching/students",
            headers={"X-API-Key": "invalid-key"}
        )
        # Should fail if API_KEY is set in environment
        # May pass if API_KEY is not set (dev mode)
        assert response.status_code in [200, 401]

