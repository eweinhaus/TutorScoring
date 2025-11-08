"""
Feature engineering service for match prediction model.
"""
from typing import Dict, Optional
from decimal import Decimal
from app.models.student import Student
from app.models.tutor import Tutor


def calculate_mismatch_scores(student: Student, tutor: Tutor) -> Dict[str, float]:
    """
    Calculate mismatch scores between student and tutor preferences.
    
    Args:
        student: Student model instance
        tutor: Tutor model instance
        
    Returns:
        Dictionary with mismatch scores:
        - pace_mismatch: Absolute difference in pace preferences (0-4)
        - style_mismatch: Binary mismatch in teaching style (0=match, 1=mismatch)
        - communication_mismatch: Absolute difference in communication style (0-4)
        - age_difference: Absolute difference in age (0+)
    """
    mismatch_scores = {}
    
    # Pace mismatch (1-5 scale)
    if student.preferred_pace is not None and tutor.preferred_pace is not None:
        mismatch_scores['pace_mismatch'] = abs(student.preferred_pace - tutor.preferred_pace)
    else:
        mismatch_scores['pace_mismatch'] = 2.5  # Default to middle if missing
    
    # Style mismatch (binary: 0 if match, 1 if different)
    if student.preferred_teaching_style and tutor.teaching_style:
        if student.preferred_teaching_style.lower() == tutor.teaching_style.lower():
            mismatch_scores['style_mismatch'] = 0.0
        else:
            mismatch_scores['style_mismatch'] = 1.0
    else:
        mismatch_scores['style_mismatch'] = 0.5  # Default to middle if missing
    
    # Communication mismatch (1-5 scale)
    if (student.communication_style_preference is not None and 
        tutor.communication_style is not None):
        mismatch_scores['communication_mismatch'] = abs(
            student.communication_style_preference - tutor.communication_style
        )
    else:
        mismatch_scores['communication_mismatch'] = 2.5  # Default to middle if missing
    
    # Age difference
    if student.age is not None and tutor.age is not None:
        mismatch_scores['age_difference'] = abs(student.age - tutor.age)
    else:
        mismatch_scores['age_difference'] = 10  # Default if missing
    
    return mismatch_scores


def calculate_compatibility_score(mismatch_scores: Dict[str, float]) -> float:
    """
    Calculate overall compatibility score from mismatch scores.
    
    Higher score = better match (0-1 scale).
    
    Args:
        mismatch_scores: Dictionary of mismatch scores
        
    Returns:
        Compatibility score (0-1), where 1 is perfect match
    """
    # Weights for each mismatch type
    weights = {
        'pace_mismatch': 0.3,
        'style_mismatch': 0.3,
        'communication_mismatch': 0.2,
        'age_difference': 0.2,
    }
    
    # Normalize each mismatch score to 0-1 scale
    # Max values: pace=4, style=1, communication=4, age=unbounded (cap at 20)
    normalized_mismatches = {
        'pace_mismatch': min(mismatch_scores['pace_mismatch'] / 4.0, 1.0),
        'style_mismatch': mismatch_scores['style_mismatch'],  # Already 0-1
        'communication_mismatch': min(mismatch_scores['communication_mismatch'] / 4.0, 1.0),
        'age_difference': min(mismatch_scores['age_difference'] / 20.0, 1.0),
    }
    
    # Calculate weighted average mismatch
    weighted_mismatch = sum(
        weights[key] * normalized_mismatches[key]
        for key in weights.keys()
    )
    
    # Compatibility is inverse of mismatch
    compatibility_score = 1.0 - weighted_mismatch
    
    # Ensure score is in valid range
    return max(0.0, min(1.0, compatibility_score))


def extract_features(student: Student, tutor: Tutor, tutor_stats: Optional[Dict] = None) -> Dict[str, float]:
    """
    Extract all features for ML model prediction.
    
    Args:
        student: Student model instance
        tutor: Tutor model instance
        tutor_stats: Optional tutor statistics (reschedule rates, etc.)
        
    Returns:
        Dictionary of feature names and values for ML model
    """
    # Calculate mismatch scores
    mismatch_scores = calculate_mismatch_scores(student, tutor)
    
    # Base features from mismatch scores
    features = mismatch_scores.copy()
    
    # Student features
    features['student_age'] = float(student.age) if student.age else 15.0
    features['student_pace'] = float(student.preferred_pace) if student.preferred_pace else 3.0
    features['student_urgency'] = float(student.urgency_level) if student.urgency_level else 3.0
    features['student_experience'] = float(student.previous_tutoring_experience) if student.previous_tutoring_experience else 0.0
    features['student_satisfaction'] = float(student.previous_satisfaction) if student.previous_satisfaction else 3.0
    
    # Tutor features
    features['tutor_age'] = float(tutor.age) if tutor.age else 30.0
    features['tutor_experience'] = float(tutor.experience_years) if tutor.experience_years else 2.0
    features['tutor_confidence'] = float(tutor.confidence_level) if tutor.confidence_level else 3.0
    features['tutor_pace'] = float(tutor.preferred_pace) if tutor.preferred_pace else 3.0
    
    # Tutor statistics (if available)
    if tutor_stats:
        features['tutor_reschedule_rate_30d'] = float(tutor_stats.get('reschedule_rate_30d', 0.0))
        features['tutor_total_sessions_30d'] = float(tutor_stats.get('total_sessions_30d', 0))
        features['tutor_is_high_risk'] = float(1.0 if tutor_stats.get('is_high_risk', False) else 0.0)
    else:
        features['tutor_reschedule_rate_30d'] = 0.0
        features['tutor_total_sessions_30d'] = 0.0
        features['tutor_is_high_risk'] = 0.0
    
    # Calculate compatibility score
    features['compatibility_score'] = calculate_compatibility_score(mismatch_scores)
    
    return features

