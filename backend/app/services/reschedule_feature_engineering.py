"""
Feature engineering service for reschedule prediction model.
"""
from typing import Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.session import Session as SessionModel
from app.models.tutor import Tutor


def extract_tutor_history_features(session: SessionModel, tutor_stats: Optional[Dict] = None) -> Dict[str, float]:
    """
    Extract tutor history features from tutor statistics.
    
    Args:
        session: Session model instance
        tutor_stats: Optional tutor statistics dictionary (from get_tutor_statistics)
        
    Returns:
        Dictionary with tutor history features:
        - tutor_reschedule_rate_7d, 30d, 90d: float (0-1, converted from percentage)
        - tutor_total_sessions_7d, 30d, 90d: int
        - tutor_is_high_risk: float (1.0 if high risk, 0.0 otherwise)
        - tutor_reschedule_trend: float (increasing=1.0, decreasing=-1.0, stable=0.0)
    """
    features = {}
    
    if tutor_stats:
        # Reschedule rates (convert from percentage to 0-1)
        # Handle None values by defaulting to 0.0
        features['tutor_reschedule_rate_7d'] = float(tutor_stats.get('reschedule_rate_7d') or 0.0) / 100.0
        features['tutor_reschedule_rate_30d'] = float(tutor_stats.get('reschedule_rate_30d') or 0.0) / 100.0
        features['tutor_reschedule_rate_90d'] = float(tutor_stats.get('reschedule_rate_90d') or 0.0) / 100.0
        
        # Total sessions
        features['tutor_total_sessions_7d'] = float(tutor_stats.get('total_sessions_7d') or 0)
        features['tutor_total_sessions_30d'] = float(tutor_stats.get('total_sessions_30d') or 0)
        features['tutor_total_sessions_90d'] = float(tutor_stats.get('total_sessions_90d') or 0)
        
        # High risk flag
        features['tutor_is_high_risk'] = float(1.0 if tutor_stats.get('is_high_risk') else 0.0)
        
        # Reschedule trend: compare 7d vs 30d rates
        rate_7d = features['tutor_reschedule_rate_7d']
        rate_30d = features['tutor_reschedule_rate_30d']
        if rate_30d > 0:
            # Trend: (7d_rate - 30d_rate) / 30d_rate
            # Positive = increasing, negative = decreasing
            trend_ratio = (rate_7d - rate_30d) / rate_30d
            # Normalize to -1 to 1 range (cap at ±1.0)
            features['tutor_reschedule_trend'] = max(-1.0, min(1.0, trend_ratio))
        else:
            # No baseline, use 0.0 (stable)
            features['tutor_reschedule_trend'] = 0.0
    else:
        # Default values if tutor_stats not available
        features['tutor_reschedule_rate_7d'] = 0.0
        features['tutor_reschedule_rate_30d'] = 0.0
        features['tutor_reschedule_rate_90d'] = 0.0
        features['tutor_total_sessions_7d'] = 0.0
        features['tutor_total_sessions_30d'] = 0.0
        features['tutor_total_sessions_90d'] = 0.0
        features['tutor_is_high_risk'] = 0.0
        features['tutor_reschedule_trend'] = 0.0
    
    return features


def extract_temporal_features(session: SessionModel) -> Dict[str, float]:
    """
    Extract temporal features from session scheduled time.
    
    Args:
        session: Session model instance
        
    Returns:
        Dictionary with temporal features:
        - day_of_week: int (0=Monday, 6=Sunday)
        - hour_of_day: int (0-23)
        - time_of_day_category: int (0=morning, 1=afternoon, 2=evening, 3=night)
        - is_weekend: float (1.0 if weekend, 0.0 otherwise)
        - days_until_session: int (if predicting before session)
        - hours_until_session: float (if predicting before session)
    """
    features = {}
    scheduled_time = session.scheduled_time
    now = datetime.utcnow()
    
    # Day of week (0=Monday, 6=Sunday)
    features['day_of_week'] = float(scheduled_time.weekday())
    
    # Hour of day (0-23)
    features['hour_of_day'] = float(scheduled_time.hour)
    
    # Time of day category
    hour = scheduled_time.hour
    if 6 <= hour < 12:
        time_category = 0.0  # morning
    elif 12 <= hour < 18:
        time_category = 1.0  # afternoon
    elif 18 <= hour < 22:
        time_category = 2.0  # evening
    else:
        time_category = 3.0  # night (22-6)
    features['time_of_day_category'] = time_category
    
    # Is weekend (Saturday=5, Sunday=6)
    weekday = scheduled_time.weekday()
    features['is_weekend'] = float(1.0 if weekday >= 5 else 0.0)
    
    # Time until session
    time_diff = scheduled_time - now
    features['days_until_session'] = float(time_diff.days)
    features['hours_until_session'] = float(time_diff.total_seconds() / 3600.0)
    
    return features


def extract_session_context_features(session: SessionModel, db: Session) -> Dict[str, float]:
    """
    Extract session context features.
    
    Args:
        session: Session model instance
        db: Database session
        
    Returns:
        Dictionary with session context features:
        - sessions_with_student_count: int (number of previous sessions with same student)
        - student_reschedule_rate: float (0-1, if student has history)
        - session_duration_minutes: int (if available)
        - consecutive_sessions_count: int (tutor's sessions on same day)
    """
    features = {}
    
    # Count previous sessions with same student
    previous_sessions = db.query(SessionModel).filter(
        and_(
            SessionModel.tutor_id == session.tutor_id,
            SessionModel.student_id == session.student_id,
            SessionModel.scheduled_time < session.scheduled_time
        )
    ).count()
    features['sessions_with_student_count'] = float(previous_sessions)
    
    # Calculate student reschedule rate (from previous sessions)
    if previous_sessions > 0:
        rescheduled_sessions = db.query(SessionModel).filter(
            and_(
                SessionModel.tutor_id == session.tutor_id,
                SessionModel.student_id == session.student_id,
                SessionModel.scheduled_time < session.scheduled_time,
                SessionModel.status == 'rescheduled'
            )
        ).count()
        features['student_reschedule_rate'] = float(rescheduled_sessions / previous_sessions)
    else:
        features['student_reschedule_rate'] = 0.0  # First-time student
    
    # Session duration (if available)
    features['session_duration_minutes'] = float(session.duration_minutes) if session.duration_minutes else 60.0  # Default 60 minutes
    
    # Count consecutive sessions on same day
    session_date = session.scheduled_time.date()
    consecutive_sessions = db.query(SessionModel).filter(
        and_(
            SessionModel.tutor_id == session.tutor_id,
            func.date(SessionModel.scheduled_time) == session_date,
            SessionModel.id != session.id  # Exclude current session
        )
    ).count()
    features['consecutive_sessions_count'] = float(consecutive_sessions)
    
    return features


def extract_tutor_characteristics(tutor: Tutor) -> Dict[str, float]:
    """
    Extract tutor characteristic features.
    
    Args:
        tutor: Tutor model instance
        
    Returns:
        Dictionary with tutor characteristics:
        - tutor_age: float
        - tutor_experience_years: float
        - tutor_confidence_level: float (1-5)
        - tutor_communication_style: float (1-5)
    """
    features = {}
    
    features['tutor_age'] = float(tutor.age) if tutor.age else 30.0
    features['tutor_experience_years'] = float(tutor.experience_years) if tutor.experience_years else 2.0
    features['tutor_confidence_level'] = float(tutor.confidence_level) if tutor.confidence_level else 3.0
    features['tutor_communication_style'] = float(tutor.communication_style) if tutor.communication_style else 3.0
    
    return features


def extract_features(session: SessionModel, tutor_stats: Optional[Dict] = None, db: Session = None) -> Dict[str, float]:
    """
    Extract all features for reschedule prediction ML model.
    
    Args:
        session: Session model instance
        tutor_stats: Optional tutor statistics dictionary
        db: Database session (required for session context features)
        
    Returns:
        Dictionary of feature names and values (all float) for ML model
        Features are sorted alphabetically for consistency
    """
    if db is None:
        raise ValueError("Database session is required for feature extraction")
    
    # Extract all feature groups
    tutor_history = extract_tutor_history_features(session, tutor_stats)
    temporal = extract_temporal_features(session)
    session_context = extract_session_context_features(session, db)
    
    # Get tutor for characteristics
    tutor = session.tutor
    if not tutor:
        # If tutor not loaded, query it
        from app.models.tutor import Tutor
        tutor = db.query(Tutor).filter(Tutor.id == session.tutor_id).first()
    
    tutor_characteristics = extract_tutor_characteristics(tutor) if tutor else {}
    
    # Combine all features
    all_features = {}
    all_features.update(tutor_history)
    all_features.update(temporal)
    all_features.update(session_context)
    all_features.update(tutor_characteristics)
    
    # Sort features alphabetically for consistency
    sorted_features = {k: all_features[k] for k in sorted(all_features.keys())}
    
    return sorted_features

