"""
Tutor service for querying tutor data.
"""
from typing import Optional, List, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func, and_
import logging

from app.models.tutor import Tutor
from app.models.tutor_score import TutorScore
from app.models.reschedule import Reschedule
from app.models.session import Session as SessionModel
from app.utils.cache import get_tutor_score, set_tutor_score

logger = logging.getLogger(__name__)


def get_tutors(
    db: Session,
    risk_status: Optional[str] = "all",
    sort_by: Optional[str] = "reschedule_rate_30d",
    sort_order: Optional[str] = "desc",
    limit: int = 100,
    offset: int = 0
) -> Tuple[List[Tutor], int]:
    """
    Get list of tutors with filtering, sorting, and pagination.
    
    Args:
        db: Database session
        risk_status: Filter by risk status ('high_risk', 'low_risk', 'all')
        sort_by: Field to sort by ('reschedule_rate_30d', 'total_sessions_30d', 'name')
        sort_order: Sort order ('asc' or 'desc')
        limit: Maximum number of results
        offset: Pagination offset
        
    Returns:
        Tuple of (list of tutors, total count)
    """
    # Start with base query - use outerjoin to include all tutors (with or without scores)
    # Then use joinedload to eagerly load the relationship for efficient access
    query = db.query(Tutor).outerjoin(TutorScore).options(joinedload(Tutor.tutor_score))
    
    # Apply risk status filter
    if risk_status == "high_risk":
        query = query.filter(TutorScore.is_high_risk == True)
    elif risk_status == "low_risk":
        query = query.filter(or_(TutorScore.is_high_risk == False, TutorScore.is_high_risk == None))
    # else: "all" - no filter
    
    # Get total count before applying sorting and pagination
    total = query.count()
    
    # Apply sorting
    if sort_by == "reschedule_rate_30d":
        if sort_order == "asc":
            query = query.order_by(TutorScore.reschedule_rate_30d.asc().nullslast())
        else:
            query = query.order_by(TutorScore.reschedule_rate_30d.desc().nullslast())
    elif sort_by == "total_sessions_30d":
        if sort_order == "asc":
            query = query.order_by(TutorScore.total_sessions_30d.asc().nullslast())
        else:
            query = query.order_by(TutorScore.total_sessions_30d.desc().nullslast())
    elif sort_by == "name":
        if sort_order == "asc":
            query = query.order_by(Tutor.name.asc())
        else:
            query = query.order_by(Tutor.name.desc())
    else:
        # Default sorting by reschedule_rate_30d
        query = query.order_by(TutorScore.reschedule_rate_30d.desc().nullslast())
    
    # Apply pagination
    tutors = query.offset(offset).limit(limit).all()
    
    return tutors, total


def get_tutor_by_id(tutor_id: str, db: Session) -> Optional[Tutor]:
    """
    Get tutor by ID with eager loading of related data.
    
    Uses caching to improve performance.
    
    Args:
        tutor_id: UUID string of the tutor
        db: Database session
        
    Returns:
        Tutor object or None if not found
    """
    # Try cache first (for tutor scores)
    cached_score = get_tutor_score(tutor_id)
    
    tutor = db.query(Tutor).options(
        joinedload(Tutor.tutor_score)
    ).filter(Tutor.id == tutor_id).first()
    
    if tutor and tutor.tutor_score and not cached_score:
        # Cache the score for future use
        score_dict = tutor.tutor_score.to_dict()
        set_tutor_score(tutor_id, score_dict)
    
    return tutor


def get_tutor_statistics(tutor_id: str, db: Session) -> dict:
    """
    Get tutor statistics (same as scores but different name for clarity).
    
    Args:
        tutor_id: UUID string of the tutor
        db: Database session
        
    Returns:
        Dictionary with statistics
    """
    tutor_score = db.query(TutorScore).filter(TutorScore.tutor_id == tutor_id).first()
    
    if not tutor_score:
        return {}
    
    return tutor_score.to_dict()


def get_tutor_history(tutor_id: str, days: int, limit: int, db: Session) -> Tuple[List[Reschedule], dict]:
    """
    Get reschedule history for a tutor with trend analysis.
    
    Args:
        tutor_id: UUID string of the tutor
        days: Number of days of history to retrieve
        limit: Maximum number of reschedules to return
        db: Database session
        
    Returns:
        Tuple of (list of reschedules, trend dictionary)
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get reschedules for this tutor
    reschedules = db.query(Reschedule).join(
        SessionModel,
        Reschedule.session_id == SessionModel.id
    ).filter(
        and_(
            SessionModel.tutor_id == tutor_id,
            Reschedule.created_at >= start_date
        )
    ).order_by(Reschedule.created_at.desc()).limit(limit).all()
    
    # Calculate weekly trends
    # Group by week and calculate reschedule rate per week
    trend_data = []
    
    # Calculate weekly buckets
    current_date = datetime.utcnow()
    for week_offset in range(days // 7, -1, -1):
        week_start = current_date - timedelta(days=week_offset * 7)
        week_end = week_start + timedelta(days=7)
        
        # Count sessions and reschedules in this week
        week_sessions = db.query(func.count(SessionModel.id)).filter(
            and_(
                SessionModel.tutor_id == tutor_id,
                SessionModel.scheduled_time >= week_start,
                SessionModel.scheduled_time < week_end
            )
        ).scalar() or 0
        
        week_reschedules = db.query(func.count(Reschedule.id)).join(
            SessionModel,
            Reschedule.session_id == SessionModel.id
        ).filter(
            and_(
                SessionModel.tutor_id == tutor_id,
                SessionModel.scheduled_time >= week_start,
                SessionModel.scheduled_time < week_end,
                Reschedule.initiator == 'tutor'
            )
        ).scalar() or 0
        
        week_rate = (week_reschedules / week_sessions * 100.0) if week_sessions > 0 else 0.0
        
        trend_data.append({
            "week": week_start.strftime("%Y-%m-%d"),
            "rate": round(week_rate, 2)
        })
    
    trend = {
        "reschedule_rate_by_week": trend_data
    }
    
    return reschedules, trend

