"""
Reschedule prediction service using trained ML model.
"""
import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session

try:
    import joblib
    import numpy as np
    import xgboost as xgb
except ImportError:
    joblib = None
    np = None
    xgb = None

from app.models.session import Session as SessionModel
from app.models.session_reschedule_prediction import SessionReschedulePrediction
from app.services.reschedule_feature_engineering import extract_features
from app.services.tutor_service import get_tutor_statistics

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
    return backend_dir / 'models' / 'reschedule_model.pkl'


def _get_feature_names_path() -> Path:
    """Get path to feature names file."""
    backend_dir = Path(__file__).parent.parent.parent
    return backend_dir / 'models' / 'reschedule_feature_names.json'


def _get_metadata_path() -> Path:
    """Get path to metadata file."""
    backend_dir = Path(__file__).parent.parent.parent
    return backend_dir / 'models' / 'reschedule_model_metadata.json'


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
            "Please run: python scripts/train_reschedule_model.py"
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
                         low_threshold: float = 0.15, 
                         high_threshold: float = 0.35) -> str:
    """
    Determine risk level from reschedule probability.
    
    Args:
        probability: Reschedule probability (0-1)
        low_threshold: Threshold for low risk (default: 0.15)
        high_threshold: Threshold for high risk (default: 0.35)
        
    Returns:
        Risk level: 'low', 'medium', or 'high'
    """
    # Allow override from environment
    low_threshold = float(os.getenv('RESCHEDULE_RISK_THRESHOLD_LOW', low_threshold))
    high_threshold = float(os.getenv('RESCHEDULE_RISK_THRESHOLD_HIGH', high_threshold))
    
    if probability < low_threshold:
        return 'low'
    elif probability < high_threshold:
        return 'medium'
    else:
        return 'high'


def predict_reschedule_probability(session: SessionModel, tutor_stats: Optional[Dict] = None, db: Session = None) -> float:
    """
    Predict reschedule probability for a session.
    
    Args:
        session: Session model instance
        tutor_stats: Optional tutor statistics dictionary
        db: Database session (required for feature extraction)
        
    Returns:
        Reschedule probability (0-1)
    """
    try:
        model, feature_names, metadata = load_model()
    except (FileNotFoundError, ImportError) as e:
        logger.error(f"Model not available: {e}")
        # Fallback: use rule-based prediction
        if tutor_stats:
            # Use tutor's reschedule rate as fallback
            rate_30d = tutor_stats.get('reschedule_rate_30d', 0.0)
            return float(rate_30d) / 100.0 if rate_30d else 0.1
        return 0.1  # Default estimate
    
    if db is None:
        raise ValueError("Database session is required for feature extraction")
    
    # Extract features
    features = extract_features(session, tutor_stats, db)
    
    # Ensure features are in correct order
    if feature_names:
        feature_vector = np.array([[features.get(name, 0.0) for name in feature_names]])
    else:
        # Fallback: use all features in sorted order
        sorted_features = sorted(features.items())
        feature_vector = np.array([[v for k, v in sorted_features]])
    
    # Predict
    probability = model.predict_proba(feature_vector)[0, 1]  # Probability of reschedule (class 1)
    
    return float(probability)


def predict_session_reschedule(session: SessionModel, tutor_stats: Optional[Dict] = None, db: Session = None) -> Dict:
    """
    Predict reschedule for a session and return full prediction.
    
    Args:
        session: Session model instance
        tutor_stats: Optional tutor statistics dictionary
        db: Database session (required for feature extraction)
        
    Returns:
        Dictionary with:
        - reschedule_probability: float (0-1)
        - risk_level: str ('low', 'medium', 'high')
        - features: Dict (for debugging)
        - model_version: str
    """
    # Calculate probability
    probability = predict_reschedule_probability(session, tutor_stats, db)
    
    # Determine risk level
    risk_level = determine_risk_level(probability)
    
    # Extract features for debugging/storage
    features = extract_features(session, tutor_stats, db) if db else {}
    
    # Get model version from metadata
    try:
        _, _, metadata = load_model()
        model_version = metadata.get('model_version', 'v1.0')
    except:
        model_version = 'v1.0'
    
    return {
        'reschedule_probability': probability,
        'risk_level': risk_level,
        'features': features,
        'model_version': model_version,
    }


def get_or_create_prediction(session: SessionModel, tutor_stats: Optional[Dict] = None, db: Session = None) -> SessionReschedulePrediction:
    """
    Get existing reschedule prediction or create new one.
    
    Args:
        session: Session model instance
        tutor_stats: Optional tutor statistics dictionary
        db: Database session (required)
        
    Returns:
        SessionReschedulePrediction model instance
    """
    if db is None:
        raise ValueError("Database session is required")
    
    # Check if prediction already exists
    existing = db.query(SessionReschedulePrediction).filter(
        SessionReschedulePrediction.session_id == session.id
    ).first()
    
    if existing:
        return existing
    
    # Generate prediction
    prediction_data = predict_session_reschedule(session, tutor_stats, db)
    
    # Create new prediction
    session_prediction = SessionReschedulePrediction(
        session_id=session.id,
        reschedule_probability=Decimal(str(prediction_data['reschedule_probability'])),
        risk_level=prediction_data['risk_level'],
        model_version=prediction_data['model_version'],
        predicted_at=datetime.utcnow(),
        features_json=prediction_data['features'],
    )
    
    db.add(session_prediction)
    db.commit()
    db.refresh(session_prediction)
    
    return session_prediction

