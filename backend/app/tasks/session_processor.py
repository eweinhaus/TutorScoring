"""
Session processing Celery tasks.
"""
import logging
from sqlalchemy.orm import Session

from app.tasks.celery_app import celery_app
from app.utils.database import SessionLocal
from app.models.session import Session as SessionModel
from app.models.tutor import Tutor
from app.services.score_service import update_scores_for_tutor
from app.tasks.email_tasks import send_email_report

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def process_session(self, session_id: str):
    """
    Process a completed session: calculate scores and send email report.
    
    This task:
    1. Fetches the session record
    2. Recalculates tutor scores (reschedule rates)
    3. Queues email report task
    
    Args:
        session_id: UUID string of the session to process
        
    Returns:
        dict: Status message with session_id
    """
    db: Session = None
    try:
        # Create new database session for this task
        db = SessionLocal()
        
        logger.info(f"Processing session {session_id}")
        
        # Fetch session record
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Fetch associated tutor
        tutor = db.query(Tutor).filter(Tutor.id == session.tutor_id).first()
        if not tutor:
            raise ValueError(f"Tutor {session.tutor_id} not found for session {session_id}")
        
        # Update tutor scores (recalculate reschedule rates)
        logger.info(f"Updating scores for tutor {tutor.id}")
        tutor_score = update_scores_for_tutor(str(tutor.id), db)
        logger.info(f"Updated scores for tutor {tutor.id}: is_high_risk={tutor_score.is_high_risk}")
        
        # Queue email report task
        try:
            send_email_report.delay(session_id)
            logger.info(f"Queued email report task for session {session_id}")
        except Exception as e:
            logger.error(f"Failed to queue email report task for session {session_id}: {str(e)}")
            # Continue anyway - score update is done
        
        logger.info(f"Successfully processed session {session_id}")
        
        return {
            "status": "success",
            "session_id": session_id,
            "tutor_id": str(tutor.id),
            "is_high_risk": tutor_score.is_high_risk
        }
        
    except Exception as exc:
        logger.error(f"Error processing session {session_id}: {str(exc)}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            countdown = 60 * (self.request.retries + 1)  # 60, 120, 180 seconds
            logger.info(f"Retrying session {session_id} in {countdown} seconds (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=exc, countdown=countdown)
        else:
            logger.error(f"Max retries exceeded for session {session_id}")
            raise exc
    
    finally:
        # Close database session
        if db:
            db.close()
