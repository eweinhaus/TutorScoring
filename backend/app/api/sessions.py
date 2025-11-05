"""
Session ingestion endpoints.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
import logging

from app.schemas.session import SessionCreate, SessionResponse
from app.utils.database import get_db
from app.services.session_service import create_session
from app.tasks.session_processor import process_session
from app.middleware.auth import get_api_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post(
    "",
    response_model=SessionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(get_api_key)]
)
async def create_session_endpoint(
    session_data: SessionCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new session and queue it for processing.
    
    This endpoint accepts session data, creates the session record,
    and queues a Celery task for background processing (score calculation
    and email report generation).
    
    Returns 202 Accepted to indicate async processing.
    """
    try:
        # Validate reschedule_info if status is 'rescheduled'
        if session_data.status == 'rescheduled' and not session_data.reschedule_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="reschedule_info is required when status is 'rescheduled'"
            )
        
        # Create session via service
        session = create_session(session_data, db)
        
        # Queue Celery task for background processing
        try:
            process_session.delay(str(session.id))
            logger.info(f"Queued session processing task for session {session.id}")
        except Exception as e:
            logger.error(f"Failed to queue Celery task for session {session.id}: {str(e)}")
            # Continue anyway - session is created, task can be retried manually
        
        # Return 202 Accepted with session data
        return SessionResponse.model_validate(session)
        
    except HTTPException:
        # Re-raise HTTPException (validation errors) without modification
        raise
    except ValueError as e:
        logger.error(f"Validation error creating session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error creating session"
        )
