"""
Reschedule rate calculation service.
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.session import Session as SessionModel
from app.models.reschedule import Reschedule


def calculate_reschedule_rate(tutor_id: str, days: int, db: Session) -> float:
    """
    Calculate reschedule rate for a tutor over a specified time window.
    
    Formula: (Tutor-Initiated Reschedules / Total Sessions) * 100
    
    Args:
        tutor_id: UUID string of the tutor
        days: Number of days for the time window (7, 30, or 90)
        db: Database session
        
    Returns:
        Reschedule rate as float (0.0 to 100.0), rounded to 2 decimal places.
        Returns 0.0 if no sessions exist in the time window.
    """
    # Calculate start date for the time window
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Count total sessions in the time window for this tutor
    total_sessions = db.query(func.count(SessionModel.id)).filter(
        and_(
            SessionModel.tutor_id == tutor_id,
            SessionModel.scheduled_time >= start_date
        )
    ).scalar() or 0
    
    # If no sessions, return 0.0
    if total_sessions == 0:
        return 0.0
    
    # Count tutor-initiated reschedules in the time window
    # Join sessions with reschedules where initiator is 'tutor'
    tutor_reschedules = db.query(func.count(Reschedule.id)).join(
        SessionModel,
        Reschedule.session_id == SessionModel.id
    ).filter(
        and_(
            SessionModel.tutor_id == tutor_id,
            SessionModel.scheduled_time >= start_date,
            Reschedule.initiator == 'tutor'
        )
    ).scalar() or 0
    
    # Calculate rate: (tutor_reschedules / total_sessions) * 100
    if total_sessions > 0:
        rate = (tutor_reschedules / total_sessions) * 100.0
        return round(rate, 2)
    
    return 0.0


def get_session_counts(tutor_id: str, days: int, db: Session) -> tuple[int, int]:
    """
    Get total sessions and tutor-initiated reschedules for a time window.
    
    Args:
        tutor_id: UUID string of the tutor
        days: Number of days for the time window
        db: Database session
        
    Returns:
        Tuple of (total_sessions, tutor_reschedules)
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Count total sessions
    total_sessions = db.query(func.count(SessionModel.id)).filter(
        and_(
            SessionModel.tutor_id == tutor_id,
            SessionModel.scheduled_time >= start_date
        )
    ).scalar() or 0
    
    # Count tutor-initiated reschedules
    tutor_reschedules = db.query(func.count(Reschedule.id)).join(
        SessionModel,
        Reschedule.session_id == SessionModel.id
    ).filter(
        and_(
            SessionModel.tutor_id == tutor_id,
            SessionModel.scheduled_time >= start_date,
            Reschedule.initiator == 'tutor'
        )
    ).scalar() or 0
    
    return total_sessions, tutor_reschedules

