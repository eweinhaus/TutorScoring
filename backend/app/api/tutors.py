"""
Tutor query endpoints.
"""
from fastapi import APIRouter, HTTPException, Query, Depends, status
from typing import Optional
from uuid import UUID
import logging

from app.schemas.tutor import (
    TutorListPaginatedResponse,
    TutorListResponse,
    TutorDetailResponse,
    TutorHistoryResponse
)
from app.schemas.tutor_score import TutorScoreResponse
from app.schemas.reschedule import RescheduleResponse
from app.utils.database import get_db
from app.services.tutor_service import (
    get_tutors,
    get_tutor_by_id,
    get_tutor_statistics,
    get_tutor_history
)
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tutors", tags=["tutors"])


@router.get("", response_model=TutorListPaginatedResponse)
async def get_tutors_endpoint(
    risk_status: Optional[str] = Query("all", description="Filter by risk status: high_risk, low_risk, all"),
    sort_by: Optional[str] = Query("reschedule_rate_30d", description="Sort field: reschedule_rate_30d, total_sessions_30d, name"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc, desc"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db)
):
    """
    Get list of tutors with filtering, sorting, and pagination.
    
    Returns tutors with their reschedule rates and risk flags.
    """
    try:
        # Validate risk_status
        if risk_status not in ["all", "high_risk", "low_risk"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="risk_status must be 'all', 'high_risk', or 'low_risk'"
            )
        
        # Validate sort_by
        if sort_by not in ["reschedule_rate_30d", "total_sessions_30d", "name"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="sort_by must be 'reschedule_rate_30d', 'total_sessions_30d', or 'name'"
            )
        
        # Validate sort_order
        if sort_order not in ["asc", "desc"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="sort_order must be 'asc' or 'desc'"
            )
        
        # Get tutors
        tutors, total = get_tutors(
            db=db,
            risk_status=risk_status,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset
        )
        
        # Convert to response models
        tutor_responses = []
        for tutor in tutors:
            tutor_score = tutor.tutor_score if hasattr(tutor, 'tutor_score') else None
            
            tutor_responses.append(TutorListResponse(
                id=tutor.id,
                name=tutor.name,
                reschedule_rate_30d=float(tutor_score.reschedule_rate_30d) if tutor_score and tutor_score.reschedule_rate_30d else None,
                is_high_risk=tutor_score.is_high_risk if tutor_score else False,
                total_sessions_30d=tutor_score.total_sessions_30d if tutor_score else 0,
                tutor_reschedules_30d=tutor_score.tutor_reschedules_30d if tutor_score else 0,
                last_calculated_at=tutor_score.last_calculated_at if tutor_score else None
            ))
        
        return TutorListPaginatedResponse(
            tutors=tutor_responses,
            total=total,
            limit=limit,
            offset=offset
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tutors: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/{tutor_id}", response_model=TutorDetailResponse)
async def get_tutor_detail_endpoint(
    tutor_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed tutor information including scores and statistics.
    """
    try:
        # Validate UUID format
        try:
            uuid_obj = UUID(tutor_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid tutor_id format (must be UUID)"
            )
        
        # Get tutor
        tutor = get_tutor_by_id(tutor_id, db)
        if not tutor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tutor with id {tutor_id} not found"
            )
        
        # Get scores
        tutor_score = tutor.tutor_score if hasattr(tutor, 'tutor_score') else None
        if not tutor_score:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tutor scores not found for tutor {tutor_id}"
            )
        
        # Get statistics (same as scores)
        statistics = get_tutor_statistics(tutor_id, db)
        
        return TutorDetailResponse(
            id=tutor.id,
            name=tutor.name,
            email=tutor.email,
            created_at=tutor.created_at,
            scores=TutorScoreResponse.model_validate(tutor_score),
            statistics=statistics
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tutor detail: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/{tutor_id}/history", response_model=TutorHistoryResponse)
async def get_tutor_history_endpoint(
    tutor_id: str,
    days: int = Query(90, ge=1, le=365, description="Number of days of history"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of reschedules"),
    db: Session = Depends(get_db)
):
    """
    Get reschedule history for a tutor with trend analysis.
    """
    try:
        # Validate UUID format
        try:
            uuid_obj = UUID(tutor_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid tutor_id format (must be UUID)"
            )
        
        # Verify tutor exists
        tutor = get_tutor_by_id(tutor_id, db)
        if not tutor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tutor with id {tutor_id} not found"
            )
        
        # Get history
        reschedules, trend = get_tutor_history(tutor_id, days, limit, db)
        
        # Convert to response models
        reschedule_responses = [
            RescheduleResponse.model_validate(r) for r in reschedules
        ]
        
        return TutorHistoryResponse(
            reschedules=reschedule_responses,
            trend=trend
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tutor history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
