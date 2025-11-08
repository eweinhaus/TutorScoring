"""
Match prediction service using trained ML model.
"""
import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict
from decimal import Decimal
from sqlalchemy.orm import Session

try:
    import joblib
    import numpy as np
    import xgboost as xgb
except ImportError:
    joblib = None
    np = None
    xgb = None

from app.models.student import Student
from app.models.tutor import Tutor
from app.models.match_prediction import MatchPrediction
from app.services.feature_engineering import extract_features, calculate_mismatch_scores, calculate_compatibility_score

logger = logging.getLogger(__name__)

# Cached model and metadata
_cached_model = None
_cached_feature_names = None
_cached_metadata = None


def clear_model_cache():
    """
    Clear the cached model to force reload from disk.
    
    Call this after retraining the model to ensure the new model is used.
    """
    global _cached_model, _cached_feature_names, _cached_metadata
    _cached_model = None
    _cached_feature_names = None
    _cached_metadata = None
    logger.info("Model cache cleared - next prediction will load new model")


def _get_model_path() -> Path:
    """Get path to model file."""
    backend_dir = Path(__file__).parent.parent.parent
    return backend_dir / 'models' / 'match_model.pkl'


def _get_feature_names_path() -> Path:
    """Get path to feature names file."""
    backend_dir = Path(__file__).parent.parent.parent
    return backend_dir / 'models' / 'feature_names.json'


def _get_metadata_path() -> Path:
    """Get path to metadata file."""
    backend_dir = Path(__file__).parent.parent.parent
    return backend_dir / 'models' / 'model_metadata.json'


def load_model():
    """
    Load model from disk (with caching).
    
    Raises:
        FileNotFoundError: If model file doesn't exist
        ImportError: If required ML libraries not installed
    """
    global _cached_model, _cached_feature_names, _cached_metadata
    
    if _cached_model is not None:
        return _cached_model, _cached_feature_names, _cached_metadata
    
    if joblib is None:
        raise ImportError(
            "ML libraries not installed. Please install: pip install xgboost scikit-learn pandas numpy joblib"
        )
    
    model_path = _get_model_path()
    if not model_path.exists():
        raise FileNotFoundError(
            f"Model file not found: {model_path}\n"
            "Please run: python scripts/train_match_model.py"
        )
    
    # Load model
    _cached_model = joblib.load(model_path)
    logger.info(f"Loaded model from {model_path}")
    
    # Load feature names
    feature_names_path = _get_feature_names_path()
    if feature_names_path.exists():
        with open(feature_names_path, 'r') as f:
            _cached_feature_names = json.load(f)
    else:
        logger.warning(f"Feature names file not found: {feature_names_path}")
        _cached_feature_names = []
    
    # Load metadata
    metadata_path = _get_metadata_path()
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            _cached_metadata = json.load(f)
    else:
        logger.warning(f"Metadata file not found: {metadata_path}")
        _cached_metadata = {}
    
    return _cached_model, _cached_feature_names, _cached_metadata


def determine_risk_level(probability: float, 
                         low_threshold: float = 0.3, 
                         high_threshold: float = 0.7) -> str:
    """
    Determine risk level from churn probability.
    
    Args:
        probability: Churn probability (0-1)
        low_threshold: Threshold for low risk (default: 0.3)
        high_threshold: Threshold for high risk (default: 0.7)
        
    Returns:
        Risk level: 'low', 'medium', or 'high'
    """
    # Allow override from environment
    low_threshold = float(os.getenv('MATCH_RISK_THRESHOLD_LOW', low_threshold))
    high_threshold = float(os.getenv('MATCH_RISK_THRESHOLD_HIGH', high_threshold))
    
    if probability < low_threshold:
        return 'low'
    elif probability < high_threshold:
        return 'medium'
    else:
        return 'high'


def predict_churn_risk(student: Student, tutor: Tutor, tutor_stats: Optional[Dict] = None) -> float:
    """
    Predict churn probability for a student-tutor match.
    
    Args:
        student: Student model instance
        tutor: Tutor model instance
        tutor_stats: Optional tutor statistics (reschedule rates, etc.)
        
    Returns:
        Churn probability (0-1)
    """
    try:
        model, feature_names, metadata = load_model()
    except (FileNotFoundError, ImportError) as e:
        logger.error(f"Model not available: {e}")
        # Fallback: use rule-based prediction
        mismatch_scores = calculate_mismatch_scores(student, tutor)
        compatibility = calculate_compatibility_score(mismatch_scores)
        # Churn probability is inverse of compatibility
        return 1.0 - compatibility
    
    # Extract features
    features = extract_features(student, tutor, tutor_stats)
    
    # Ensure features are in correct order
    if feature_names:
        feature_vector = np.array([[features.get(name, 0.0) for name in feature_names]])
    else:
        # Fallback: use all features
        feature_vector = np.array([[v for v in features.values()]])
    
    # Predict
    probability = model.predict_proba(feature_vector)[0, 1]  # Probability of churn (class 1)
    
    return float(probability)


def predict_match(student: Student, tutor: Tutor, tutor_stats: Optional[Dict] = None) -> Dict:
    """
    Predict match quality and return full prediction.
    
    Args:
        student: Student model instance
        tutor: Tutor model instance
        tutor_stats: Optional tutor statistics
        
    Returns:
        Dictionary with:
        - churn_probability: float (0-1)
        - risk_level: str ('low', 'medium', 'high')
        - compatibility_score: float (0-1)
        - mismatch_scores: dict
    """
    # Calculate mismatch scores
    mismatch_scores = calculate_mismatch_scores(student, tutor)
    
    # Calculate compatibility
    compatibility_score = calculate_compatibility_score(mismatch_scores)
    
    # Predict churn risk
    churn_probability = predict_churn_risk(student, tutor, tutor_stats)
    
    # Determine risk level
    risk_level = determine_risk_level(churn_probability)
    
    return {
        'churn_probability': churn_probability,
        'risk_level': risk_level,
        'compatibility_score': compatibility_score,
        'mismatch_scores': mismatch_scores,
    }


def get_or_create_match_prediction(
    db: Session,
    student: Student,
    tutor: Tutor,
    tutor_stats: Optional[Dict] = None,
    force_refresh: bool = False
) -> MatchPrediction:
    """
    Get existing match prediction or create new one.
    
    Args:
        db: Database session
        student: Student model instance
        tutor: Tutor model instance
        tutor_stats: Optional tutor statistics
        force_refresh: If True, recalculate existing predictions (default: False)
        
    Returns:
        MatchPrediction model instance
    """
    # Check if prediction already exists
    existing = db.query(MatchPrediction).filter(
        MatchPrediction.student_id == student.id,
        MatchPrediction.tutor_id == tutor.id
    ).first()
    
    # Generate prediction
    prediction_data = predict_match(student, tutor, tutor_stats)
    
    if existing:
        if force_refresh:
            # Update existing prediction with new data
            existing.churn_probability = Decimal(str(prediction_data['churn_probability']))
            existing.risk_level = prediction_data['risk_level']
            existing.compatibility_score = Decimal(str(prediction_data['compatibility_score']))
            existing.pace_mismatch = Decimal(str(prediction_data['mismatch_scores']['pace_mismatch']))
            existing.style_mismatch = Decimal(str(prediction_data['mismatch_scores']['style_mismatch']))
            existing.communication_mismatch = Decimal(str(prediction_data['mismatch_scores']['communication_mismatch']))
            existing.age_difference = int(prediction_data['mismatch_scores']['age_difference'])
            # Clear AI explanation since prediction changed
            existing.ai_explanation = None
            db.commit()
            db.refresh(existing)
            logger.info(f"Refreshed match prediction for student {student.id} and tutor {tutor.id}")
            return existing
        else:
            return existing
    
    # Create new prediction
    match_prediction = MatchPrediction(
        student_id=student.id,
        tutor_id=tutor.id,
        churn_probability=Decimal(str(prediction_data['churn_probability'])),
        risk_level=prediction_data['risk_level'],
        compatibility_score=Decimal(str(prediction_data['compatibility_score'])),
        pace_mismatch=Decimal(str(prediction_data['mismatch_scores']['pace_mismatch'])),
        style_mismatch=Decimal(str(prediction_data['mismatch_scores']['style_mismatch'])),
        communication_mismatch=Decimal(str(prediction_data['mismatch_scores']['communication_mismatch'])),
        age_difference=int(prediction_data['mismatch_scores']['age_difference']),
        model_version='v1.0',
    )
    
    db.add(match_prediction)
    db.commit()
    db.refresh(match_prediction)
    
    return match_prediction


def refresh_tutor_predictions(db: Session, tutor_id: str) -> int:
    """
    Refresh all match predictions for a specific tutor.
    
    This should be called when tutor data or tutor_stats change.
    
    Args:
        db: Database session
        tutor_id: Tutor UUID string
        
    Returns:
        Number of predictions refreshed
    """
    from app.models.student import Student
    from app.models.tutor import Tutor
    
    tutor = db.query(Tutor).filter(Tutor.id == tutor_id).first()
    if not tutor:
        logger.warning(f"Tutor {tutor_id} not found for prediction refresh")
        return 0
    
    # Get tutor stats
    tutor_stats = None
    if tutor.tutor_score:
        tutor_stats = {
            'reschedule_rate_30d': float(tutor.tutor_score.reschedule_rate_30d or 0),
            'total_sessions_30d': tutor.tutor_score.total_sessions_30d,
            'is_high_risk': tutor.tutor_score.is_high_risk,
        }
    
    # Get all students
    students = db.query(Student).all()
    
    refreshed_count = 0
    for student in students:
        # Force refresh existing prediction
        get_or_create_match_prediction(db, student, tutor, tutor_stats, force_refresh=True)
        refreshed_count += 1
    
    logger.info(f"Refreshed {refreshed_count} match predictions for tutor {tutor_id}")
    return refreshed_count


def refresh_student_predictions(db: Session, student_id: str) -> int:
    """
    Refresh all match predictions for a specific student.
    
    This should be called when student data changes.
    
    Args:
        db: Database session
        student_id: Student UUID string
        
    Returns:
        Number of predictions refreshed
    """
    from app.models.student import Student
    from app.models.tutor import Tutor
    
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        logger.warning(f"Student {student_id} not found for prediction refresh")
        return 0
    
    # Get all tutors
    tutors = db.query(Tutor).all()
    
    refreshed_count = 0
    for tutor in tutors:
        # Get tutor stats
        tutor_stats = None
        if tutor.tutor_score:
            tutor_stats = {
                'reschedule_rate_30d': float(tutor.tutor_score.reschedule_rate_30d or 0),
                'total_sessions_30d': tutor.tutor_score.total_sessions_30d,
                'is_high_risk': tutor.tutor_score.is_high_risk,
            }
        
        # Force refresh existing prediction
        get_or_create_match_prediction(db, student, tutor, tutor_stats, force_refresh=True)
        refreshed_count += 1
    
    logger.info(f"Refreshed {refreshed_count} match predictions for student {student_id}")
    return refreshed_count


def refresh_all_predictions(db: Session) -> int:
    """
    Refresh all match predictions in the database.
    
    This should be called when model is retrained or when data changes significantly.
    
    Args:
        db: Database session
        
    Returns:
        Total number of predictions refreshed
    """
    from app.models.student import Student
    from app.models.tutor import Tutor
    
    students = db.query(Student).all()
    tutors = db.query(Tutor).all()
    
    total_refreshed = 0
    for tutor in tutors:
        # Get tutor stats
        tutor_stats = None
        if tutor.tutor_score:
            tutor_stats = {
                'reschedule_rate_30d': float(tutor.tutor_score.reschedule_rate_30d or 0),
                'total_sessions_30d': tutor.tutor_score.total_sessions_30d,
                'is_high_risk': tutor.tutor_score.is_high_risk,
            }
        
        for student in students:
            get_or_create_match_prediction(db, student, tutor, tutor_stats, force_refresh=True)
            total_refreshed += 1
    
    logger.info(f"Refreshed {total_refreshed} match predictions total")
    return total_refreshed

