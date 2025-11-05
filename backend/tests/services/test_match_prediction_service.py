"""
Tests for match prediction service.
"""
import pytest
from decimal import Decimal

from app.services.match_prediction_service import (
    determine_risk_level,
    predict_churn_risk,
    predict_match,
    get_or_create_match_prediction
)
from app.models.student import Student
from app.models.tutor import Tutor


class TestRiskLevel:
    """Test risk level determination."""
    
    def test_determine_risk_level_low(self):
        """Test low risk level."""
        assert determine_risk_level(0.2) == "low"
        assert determine_risk_level(0.29) == "low"
    
    def test_determine_risk_level_medium(self):
        """Test medium risk level."""
        assert determine_risk_level(0.3) == "medium"
        assert determine_risk_level(0.5) == "medium"
        assert determine_risk_level(0.69) == "medium"
    
    def test_determine_risk_level_high(self):
        """Test high risk level."""
        assert determine_risk_level(0.7) == "high"
        assert determine_risk_level(0.9) == "high"
        assert determine_risk_level(1.0) == "high"


class TestPredictMatch:
    """Test match prediction."""
    
    def test_predict_match_returns_dict(self, db_session):
        """Test that predict_match returns a dictionary with expected keys."""
        student = Student(
            name="Test Student",
            age=15,
            preferred_pace=3,
            preferred_teaching_style="structured",
            communication_style_preference=3,
            urgency_level=3,
        )
        db_session.add(student)
        db_session.commit()
        
        tutor = Tutor(
            name="Test Tutor",
            age=30,
            preferred_pace=3,
            teaching_style="structured",
            communication_style=3,
        )
        db_session.add(tutor)
        db_session.commit()
        
        prediction = predict_match(student, tutor)
        
        assert isinstance(prediction, dict)
        assert "churn_probability" in prediction
        assert "risk_level" in prediction
        assert "compatibility_score" in prediction
        assert "mismatch_scores" in prediction
        assert prediction["risk_level"] in ["low", "medium", "high"]
        assert 0.0 <= prediction["churn_probability"] <= 1.0
        assert 0.0 <= prediction["compatibility_score"] <= 1.0
    
    def test_get_or_create_match_prediction(self, db_session):
        """Test getting or creating match prediction."""
        student = Student(
            name="Test Student",
            age=15,
            preferred_pace=3,
            preferred_teaching_style="structured",
            communication_style_preference=3,
            urgency_level=3,
        )
        db_session.add(student)
        db_session.commit()
        
        tutor = Tutor(
            name="Test Tutor",
            age=30,
            preferred_pace=3,
            teaching_style="structured",
            communication_style=3,
        )
        db_session.add(tutor)
        db_session.commit()
        
        # Create prediction
        prediction = get_or_create_match_prediction(db_session, student, tutor)
        
        assert prediction is not None
        assert prediction.student_id == student.id
        assert prediction.tutor_id == tutor.id
        assert prediction.churn_probability is not None
        assert prediction.risk_level in ["low", "medium", "high"]
        
        # Get existing prediction (should return same)
        prediction2 = get_or_create_match_prediction(db_session, student, tutor)
        assert prediction.id == prediction2.id

