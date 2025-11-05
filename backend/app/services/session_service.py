"""
Session service for creating and managing sessions.
"""
import uuid
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.session import Session as SessionModel
from app.models.reschedule import Reschedule
from app.models.tutor import Tutor
from app.schemas.session import SessionCreate


def create_session(session_data: SessionCreate, db: Session) -> SessionModel:
    """
    Create a new session record and associated reschedule if applicable.
    
    Args:
        session_data: SessionCreate schema with session data
        db: Database session
        
    Returns:
        Created Session record
        
    Raises:
        ValueError: If session_id is duplicate or tutor_id is invalid
        IntegrityError: If database constraint is violated
    """
    # Note: Validation of reschedule_info is handled in API layer (sessions.py)
    # This service layer focuses on business logic only
    
    # Check if session with this ID already exists
    existing_session = db.query(SessionModel).filter(
        SessionModel.id == session_data.session_id
    ).first()
    
    if existing_session:
        raise ValueError(f"Session with id {session_data.session_id} already exists")
    
    # Get or create tutor
    tutor = db.query(Tutor).filter(Tutor.id == session_data.tutor_id).first()
    if not tutor:
        # Create tutor if it doesn't exist (per PRD requirement)
        tutor = Tutor(
            id=session_data.tutor_id,
            name=f"Tutor {str(session_data.tutor_id)[:8]}",  # Default name
            is_active=True
        )
        db.add(tutor)
        db.flush()  # Flush to get tutor ID
    
    # Create session record
    session = SessionModel(
        id=session_data.session_id,
        tutor_id=session_data.tutor_id,
        student_id=session_data.student_id,
        scheduled_time=session_data.scheduled_time,
        completed_time=session_data.completed_time,
        status=session_data.status,
        duration_minutes=session_data.duration_minutes
    )
    
    db.add(session)
    db.flush()  # Flush to get session ID
    
    # Create reschedule record if status is 'rescheduled'
    if session_data.status == 'rescheduled' and session_data.reschedule_info:
        reschedule_info = session_data.reschedule_info
        
        # Calculate hours_before_session
        hours_before = None
        if reschedule_info.cancelled_at and reschedule_info.original_time:
            delta = reschedule_info.original_time - reschedule_info.cancelled_at
            hours_before = delta.total_seconds() / 3600.0
        
        reschedule = Reschedule(
            session_id=session.id,
            initiator=reschedule_info.initiator,
            original_time=reschedule_info.original_time,
            new_time=reschedule_info.new_time,
            reason=reschedule_info.reason,
            reason_code=reschedule_info.reason_code,
            cancelled_at=reschedule_info.cancelled_at,
            hours_before_session=hours_before
        )
        
        db.add(reschedule)
    
    # Commit transaction
    try:
        db.commit()
        db.refresh(session)
        return session
    except IntegrityError as e:
        db.rollback()
        raise ValueError(f"Database constraint violation: {str(e)}") from e

