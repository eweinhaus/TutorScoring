"""
Email sending Celery tasks.
"""
import os
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from app.tasks.celery_app import celery_app
from app.utils.database import SessionLocal
from app.models.email_report import EmailReport
from app.services.email_report_service import send_session_report

logger = logging.getLogger(__name__)
load_dotenv()


@celery_app.task(bind=True, max_retries=3)
def send_email_report(self, session_id: str):
    """
    Send email report for a session.
    
    This task:
    1. Generates email report content
    2. Sends email via email service
    3. Creates EmailReport record
    
    Args:
        session_id: UUID string of the session
        
    Returns:
        dict: Status message with session_id and email status
    """
    db: Session = None
    try:
        # Create new database session for this task
        db = SessionLocal()
        
        logger.info(f"Sending email report for session {session_id}")
        
        # Get recipient email from environment
        recipient_email = os.getenv("ADMIN_EMAIL")
        if not recipient_email:
            raise ValueError("ADMIN_EMAIL environment variable is not set")
        
        # Send email report
        success = send_session_report(session_id, recipient_email, db)
        
        # Create EmailReport record
        email_report = EmailReport(
            session_id=session_id,
            recipient_email=recipient_email,
            sent_at=datetime.utcnow(),  # Always set timestamp, even for failures (audit trail)
            status="sent" if success else "failed",
            error_message=None
        )
        
        db.add(email_report)
        db.commit()
        db.refresh(email_report)
        
        if success:
            logger.info(f"Email report sent successfully for session {session_id}")
            return {
                "status": "success",
                "session_id": session_id,
                "email_report_id": str(email_report.id)
            }
        else:
            logger.error(f"Failed to send email report for session {session_id}")
            return {
                "status": "failed",
                "session_id": session_id,
                "email_report_id": str(email_report.id)
            }
        
    except Exception as exc:
        logger.error(f"Error sending email report for session {session_id}: {str(exc)}")
        
        # Create failed EmailReport record
        if db:
            try:
                recipient_email = os.getenv("ADMIN_EMAIL", "unknown")
                email_report = EmailReport(
                    session_id=session_id,
                    recipient_email=recipient_email,
                    sent_at=datetime.utcnow(),  # Always set timestamp, even for failures (audit trail)
                    status="failed",
                    error_message=str(exc)
                )
                db.add(email_report)
                db.commit()
            except Exception as e:
                logger.error(f"Failed to create EmailReport record: {str(e)}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            countdown = 60 * (self.request.retries + 1)  # 60, 120, 180 seconds
            logger.info(f"Retrying email report for session {session_id} in {countdown} seconds (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=exc, countdown=countdown)
        else:
            logger.error(f"Max retries exceeded for email report session {session_id}")
            raise exc
    
    finally:
        # Close database session
        if db:
            db.close()
