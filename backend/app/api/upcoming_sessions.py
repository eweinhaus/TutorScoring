"""
Upcoming sessions endpoints with reschedule predictions.
"""
from typing import Optional, List
from datetime import datetime, timedelta
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Depends, Query, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import logging

from app.schemas.session_reschedule_prediction import SessionReschedulePredictionResponse
from app.services.reschedule_prediction_service import get_or_create_prediction
from app.services.tutor_service import get_tutor_statistics
from app.models.session import Session as SessionModel
from app.models.session_reschedule_prediction import SessionReschedulePrediction
from app.utils.database import get_db
from app.middleware.auth import get_api_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upcoming-sessions", tags=["upcoming-sessions"])


class BatchPredictRequest(BaseModel):
    """Request model for batch prediction."""
    session_ids: Optional[List[UUID]] = None
    days_ahead: Optional[int] = None


@router.get("")
async def get_upcoming_sessions(
    days_ahead: int = Query(default=7, ge=1, le=90, description="Number of days ahead to show"),
    risk_level: Optional[str] = Query(default=None, description="Filter by risk level (low/medium/high)"),
    tutor_id: Optional[UUID] = Query(default=None, description="Filter by tutor ID"),
    limit: int = Query(default=50, ge=1, le=500, description="Pagination limit"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    sort_by: str = Query(default="scheduled_time", description="Sort field"),
    sort_order: str = Query(default="asc", description="Sort order (asc/desc)"),
    db: Session = Depends(get_db),
    _: bool = Depends(get_api_key)
):
    """
    Get upcoming sessions with reschedule predictions.
    
    Returns all upcoming (not completed) sessions with their reschedule probabilities
    and risk levels.
    """
    try:
        # Calculate time range
        now = datetime.utcnow()
        end_date = now + timedelta(days=days_ahead)
        
        # Build base query with eager loading
        from app.models.tutor import Tutor
        from app.models.student import Student
        from sqlalchemy.orm import joinedload
        import uuid
        
        query = db.query(SessionModel).options(
            joinedload(SessionModel.tutor)
        ).filter(
            SessionModel.scheduled_time >= now,
            SessionModel.scheduled_time <= end_date,
            SessionModel.status != 'completed'
        )
        
        # Filter by tutor_id if provided
        if tutor_id:
            query = query.filter(SessionModel.tutor_id == tutor_id)
        
        # Filter by risk_level if provided (need to join predictions for filtering)
        if risk_level:
            if risk_level not in ['low', 'medium', 'high']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid risk_level: {risk_level}. Must be 'low', 'medium', or 'high'"
                )
            query = query.join(
                SessionReschedulePrediction,
                SessionReschedulePrediction.session_id == SessionModel.id
            ).filter(SessionReschedulePrediction.risk_level == risk_level)
        
        # Get total count before pagination
        total = query.count()
        
        # Apply sorting - handle different sort fields
        # Note: We'll sort in memory for reschedule_probability, tutor_name, and student_name/student_id to avoid complex joins
        if sort_by == "scheduled_time":
            sort_column = SessionModel.scheduled_time
        elif sort_by == "student_id":
            # Sort by student_name when available, fallback to student_id
            # Will sort in memory after fetching student names
            sort_column = SessionModel.scheduled_time
        elif sort_by == "reschedule_probability":
            # For probability sorting, we'll need to join predictions
            # But we'll handle this after fetching to avoid query complexity
            sort_column = SessionModel.scheduled_time  # Default sort, will sort in memory
        elif sort_by == "tutor_name":
            # Tutor is already loaded via joinedload, sort by session time for now
            # Will sort in memory by tutor name
            sort_column = SessionModel.scheduled_time
        elif sort_by == "student_name":
            # Student name requires lookup, sort by session time for now
            # Will sort in memory by student name
            sort_column = SessionModel.scheduled_time
        else:
            sort_column = SessionModel.scheduled_time
        
        if sort_order.lower() == "desc":
            query = query.order_by(sort_column.desc(), SessionModel.id.desc())  # Secondary sort for consistency
        else:
            query = query.order_by(sort_column.asc(), SessionModel.id.asc())  # Secondary sort for consistency
        
        # Apply pagination - fetch more than needed if we need to sort in memory
        # For simple sorts, use normal pagination
        if sort_by == "scheduled_time":
            sessions = query.offset(offset).limit(limit).all()
        else:
            # For complex sorts (probability, tutor_name, student_name, student_id), fetch all then sort
            sessions = query.all()
        
        # For each session, get or create prediction
        result_sessions = []
        for session in sessions:
            # Get tutor
            tutor = session.tutor
            if not tutor:
                continue
            
            # Get tutor stats
            tutor_stats = get_tutor_statistics(str(tutor.id), db)
            
            # Get or create prediction
            try:
                # Check if we need to refresh (if model version changed)
                from app.services.reschedule_prediction_service import load_model
                _, _, _, metadata = load_model()
                current_model_version = metadata.get('model_version', 'v1.0')
                
                # Check existing prediction
                from app.models.session_reschedule_prediction import SessionReschedulePrediction
                existing_pred = db.query(SessionReschedulePrediction).filter(
                    SessionReschedulePrediction.session_id == session.id
                ).first()
                
                # Force refresh if model version changed or prediction doesn't exist
                force_refresh = (
                    existing_pred is None or 
                    existing_pred.model_version != current_model_version
                )
                
                prediction = get_or_create_prediction(session, tutor_stats, db, force_refresh=force_refresh)
                reschedule_probability = float(prediction.reschedule_probability)
                risk_level_value = prediction.risk_level
                predicted_at = prediction.predicted_at
            except Exception as e:
                logger.warning(f"Error generating prediction for session {session.id}: {e}")
                # Fallback values
                reschedule_probability = 0.1
                risk_level_value = 'low'
                predicted_at = datetime.utcnow()
            
            # Try to get student name if student_id is a valid UUID
            student_name = None
            try:
                # Try to parse student_id as UUID
                student_uuid = uuid.UUID(session.student_id)
                student = db.query(Student).filter(Student.id == student_uuid).first()
                if student:
                    student_name = student.name
            except (ValueError, TypeError):
                # student_id is not a valid UUID, skip lookup
                pass
            
            result_sessions.append({
                "id": str(session.id),
                "tutor_id": str(session.tutor_id),
                "tutor_name": tutor.name if tutor else "Unknown",
                "student_id": session.student_id,
                "student_name": student_name,
                "scheduled_time": session.scheduled_time.isoformat(),
                "status": session.status,
                "reschedule_probability": reschedule_probability,
                "risk_level": risk_level_value,
                "predicted_at": predicted_at.isoformat() if predicted_at else None,
            })
        
        # Apply in-memory sorting for complex sort fields
        if sort_by == "reschedule_probability":
            result_sessions.sort(
                key=lambda x: x["reschedule_probability"],
                reverse=(sort_order.lower() == "desc")
            )
        elif sort_by == "tutor_name":
            result_sessions.sort(
                key=lambda x: x["tutor_name"] or "",
                reverse=(sort_order.lower() == "desc")
            )
        elif sort_by == "student_id" or sort_by == "student_name":
            # Sort by student_name when available, fallback to student_id
            result_sessions.sort(
                key=lambda x: x.get("student_name") or x.get("student_id") or "",
                reverse=(sort_order.lower() == "desc")
            )
        
        # Apply pagination if we sorted in memory
        if sort_by != "scheduled_time":
            result_sessions = result_sessions[offset:offset + limit]
        
        return {
            "sessions": result_sessions,
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching upcoming sessions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching upcoming sessions: {str(e)}"
        )


@router.get("/{session_id}/predict")
async def get_session_prediction(
    session_id: UUID,
    db: Session = Depends(get_db),
    _: bool = Depends(get_api_key)
):
    """
    Get or refresh reschedule prediction for a specific session.
    
    Only works for upcoming sessions.
    """
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found"
        )
    
    # Check if session is upcoming
    if session.scheduled_time < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prediction only available for upcoming sessions"
        )
    
    # Get tutor stats
    tutor = session.tutor
    if not tutor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tutor not found for session"
        )
    
    tutor_stats = get_tutor_statistics(str(tutor.id), db)
    
    # Generate or refresh prediction
    try:
        prediction = get_or_create_prediction(session, tutor_stats, db)
        
        return {
            "session_id": str(session.id),
            "reschedule_probability": float(prediction.reschedule_probability),
            "risk_level": prediction.risk_level,
            "model_version": prediction.model_version,
            "predicted_at": prediction.predicted_at.isoformat(),
            "features": prediction.features_json,
        }
    except Exception as e:
        logger.error(f"Error generating prediction for session {session_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating prediction: {str(e)}"
        )


@router.post("/batch-predict")
async def batch_predict_sessions(
    request_data: BatchPredictRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(get_api_key)
):
    """
    Generate predictions for multiple sessions.
    
    Request body should contain either:
    - {"session_ids": [uuid1, uuid2, ...]} OR
    - {"days_ahead": 7}
    """
    try:
        session_ids = request_data.session_ids
        days_ahead = request_data.days_ahead
        
        if session_ids:
            sessions = db.query(SessionModel).filter(SessionModel.id.in_(session_ids)).all()
        elif days_ahead:
            now = datetime.utcnow()
            end_date = now + timedelta(days=days_ahead)
            sessions = db.query(SessionModel).filter(
                SessionModel.scheduled_time >= now,
                SessionModel.scheduled_time <= end_date,
                SessionModel.status != 'completed'
            ).all()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either session_ids or days_ahead must be provided"
            )
        
        predicted = 0
        errors = 0
        
        for session in sessions:
            try:
                tutor = session.tutor
                if not tutor:
                    errors += 1
                    continue
                
                tutor_stats = get_tutor_statistics(str(tutor.id), db)
                get_or_create_prediction(session, tutor_stats, db)
                predicted += 1
            except Exception as e:
                logger.warning(f"Error predicting session {session.id}: {e}")
                errors += 1
        
        return {
            "predicted": predicted,
            "errors": errors,
            "total": len(sessions),
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch prediction: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in batch prediction: {str(e)}"
        )

