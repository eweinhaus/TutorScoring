"""
Score update service for tutor risk scoring.
"""
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.tutor_score import TutorScore
from app.models.tutor import Tutor
from app.services.reschedule_calculator import calculate_reschedule_rate, get_session_counts
from app.utils.cache import invalidate_tutor_score


def update_scores_for_tutor(tutor_id: str, db: Session, risk_threshold: float = 15.0) -> TutorScore:
    """
    Update all reschedule rates and risk flags for a tutor.
    
    Calculates rates for 7-day, 30-day, and 90-day windows and updates
    the TutorScore record. Sets is_high_risk flag if any rate exceeds threshold.
    
    Args:
        tutor_id: UUID string of the tutor
        db: Database session
        risk_threshold: Risk threshold percentage (default 15.0)
        
    Returns:
        Updated TutorScore record
        
    Raises:
        ValueError: If tutor_id is invalid
    """
    # Verify tutor exists
    tutor = db.query(Tutor).filter(Tutor.id == tutor_id).first()
    if not tutor:
        raise ValueError(f"Tutor with id {tutor_id} not found")
    
    # Calculate rates for all time windows
    rate_7d = calculate_reschedule_rate(tutor_id, 7, db)
    rate_30d = calculate_reschedule_rate(tutor_id, 30, db)
    rate_90d = calculate_reschedule_rate(tutor_id, 90, db)
    
    # Get counts for all time windows
    total_7d, reschedules_7d = get_session_counts(tutor_id, 7, db)
    total_30d, reschedules_30d = get_session_counts(tutor_id, 30, db)
    total_90d, reschedules_90d = get_session_counts(tutor_id, 90, db)
    
    # Get or create TutorScore record
    tutor_score = db.query(TutorScore).filter(TutorScore.tutor_id == tutor_id).first()
    
    if not tutor_score:
        tutor_score = TutorScore(
            tutor_id=tutor_id,
            risk_threshold=Decimal(str(risk_threshold))
        )
        db.add(tutor_score)
    
    # Update all score fields
    tutor_score.update_rates(
        rates_7d=rate_7d,
        rates_30d=rate_30d,
        rates_90d=rate_90d,
        counts_7d=total_7d,
        counts_30d=total_30d,
        counts_90d=total_90d,
        reschedules_7d=reschedules_7d,
        reschedules_30d=reschedules_30d,
        reschedules_90d=reschedules_90d
    )
    
    # Commit transaction
    db.commit()
    db.refresh(tutor_score)
    
    # Invalidate cache
    invalidate_tutor_score(tutor_id)
    
    return tutor_score


def check_risk_flag(tutor_id: str, threshold: float, db: Session) -> bool:
    """
    Check and update risk flag for a tutor.
    
    Args:
        tutor_id: UUID string of the tutor
        threshold: Risk threshold percentage
        db: Database session
        
    Returns:
        True if tutor is high risk, False otherwise
    """
    tutor_score = db.query(TutorScore).filter(TutorScore.tutor_id == tutor_id).first()
    
    if not tutor_score:
        return False
    
    # Update risk flag
    tutor_score.check_risk_flag()
    db.commit()
    
    return tutor_score.is_high_risk

