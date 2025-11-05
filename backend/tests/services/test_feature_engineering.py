"""
Tests for feature engineering service.
"""
import pytest
from decimal import Decimal

from app.services.feature_engineering import (
    calculate_mismatch_scores,
    calculate_compatibility_score,
    extract_features
)
from app.models.student import Student
from app.models.tutor import Tutor


@pytest.fixture
def sample_student():
    """Create a sample student."""
    return Student(
        id=None,
        name="Test Student",
        age=15,
        preferred_pace=3,
        preferred_teaching_style="structured",
        communication_style_preference=3,
        urgency_level=3,
        previous_tutoring_experience=5,
    )


@pytest.fixture
def sample_tutor():
    """Create a sample tutor."""
    return Tutor(
        id=None,
        name="Test Tutor",
        age=30,
        experience_years=5,
        teaching_style="structured",
        preferred_pace=3,
        communication_style=3,
        confidence_level=4,
    )


class TestMismatchScores:
    """Test mismatch score calculations."""
    
    def test_calculate_mismatch_scores_perfect_match(self, sample_student, sample_tutor):
        """Test mismatch scores for perfect match."""
        scores = calculate_mismatch_scores(sample_student, sample_tutor)
        
        assert scores["pace_mismatch"] == 0.0
        assert scores["style_mismatch"] == 0.0
        assert scores["communication_mismatch"] == 0.0
        assert scores["age_difference"] == 15  # 30 - 15
    
    def test_calculate_mismatch_scores_with_differences(self, sample_student, sample_tutor):
        """Test mismatch scores with differences."""
        sample_student.preferred_pace = 5
        sample_tutor.preferred_pace = 1
        sample_student.preferred_teaching_style = "flexible"
        sample_tutor.teaching_style = "structured"
        sample_student.communication_style_preference = 5
        sample_tutor.communication_style = 1
        
        scores = calculate_mismatch_scores(sample_student, sample_tutor)
        
        assert scores["pace_mismatch"] == 4.0
        assert scores["style_mismatch"] == 1.0
        assert scores["communication_mismatch"] == 4.0
    
    def test_calculate_mismatch_scores_with_missing_data(self):
        """Test mismatch scores with missing tutor data."""
        student = Student(
            id=None,
            name="Test Student",
            age=15,
            preferred_pace=3,
            preferred_teaching_style="structured",
            communication_style_preference=3,
            urgency_level=3,
        )
        tutor = Tutor(
            id=None,
            name="Test Tutor",
            # Missing preferences
        )
        
        scores = calculate_mismatch_scores(student, tutor)
        
        # Should use defaults
        assert "pace_mismatch" in scores
        assert "style_mismatch" in scores
        assert "communication_mismatch" in scores
        assert "age_difference" in scores


class TestCompatibilityScore:
    """Test compatibility score calculations."""
    
    def test_calculate_compatibility_perfect_match(self, sample_student, sample_tutor):
        """Test compatibility for perfect match."""
        mismatch_scores = calculate_mismatch_scores(sample_student, sample_tutor)
        compatibility = calculate_compatibility_score(mismatch_scores)
        
        # Perfect match should have high compatibility (not exactly 1.0 due to age difference)
        assert compatibility > 0.7
        assert compatibility <= 1.0
    
    def test_calculate_compatibility_poor_match(self):
        """Test compatibility for poor match."""
        student = Student(
            id=None,
            name="Test Student",
            age=15,
            preferred_pace=5,
            preferred_teaching_style="flexible",
            communication_style_preference=5,
            urgency_level=3,
        )
        tutor = Tutor(
            id=None,
            name="Test Tutor",
            age=45,
            preferred_pace=1,
            teaching_style="structured",
            communication_style=1,
        )
        
        mismatch_scores = calculate_mismatch_scores(student, tutor)
        compatibility = calculate_compatibility_score(mismatch_scores)
        
        # Poor match should have low compatibility
        assert compatibility < 0.5
        assert compatibility >= 0.0


class TestExtractFeatures:
    """Test feature extraction."""
    
    def test_extract_features(self, sample_student, sample_tutor):
        """Test feature extraction."""
        features = extract_features(sample_student, sample_tutor)
        
        assert "pace_mismatch" in features
        assert "style_mismatch" in features
        assert "communication_mismatch" in features
        assert "age_difference" in features
        assert "student_age" in features
        assert "tutor_age" in features
        assert "compatibility_score" in features
    
    def test_extract_features_with_tutor_stats(self, sample_student, sample_tutor):
        """Test feature extraction with tutor statistics."""
        tutor_stats = {
            "reschedule_rate_30d": 10.5,
            "total_sessions_30d": 50,
            "is_high_risk": False,
        }
        
        features = extract_features(sample_student, sample_tutor, tutor_stats)
        
        assert "tutor_reschedule_rate_30d" in features
        assert features["tutor_reschedule_rate_30d"] == 10.5
        assert features["tutor_total_sessions_30d"] == 50
        assert features["tutor_is_high_risk"] == 0.0

