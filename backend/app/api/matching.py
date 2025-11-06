"""
Matching service API endpoints.
"""
from fastapi import APIRouter, HTTPException, Query, Depends, Path, Body, status
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field
import logging

from app.schemas.student import (
    StudentCreate,
    StudentResponse,
    StudentListResponse,
    StudentListPaginatedResponse
)
from app.schemas.match_prediction import (
    MatchPredictionResponse,
    MatchPredictionWithDetails,
    MatchPredictionListResponse
)
from app.schemas.tutor import TutorListResponse
from app.utils.database import get_db
from app.middleware.auth import verify_api_key
from app.models.student import Student
from app.models.tutor import Tutor
from app.models.match_prediction import MatchPrediction
from app.services.match_prediction_service import (
    get_or_create_match_prediction,
    refresh_tutor_predictions,
    refresh_student_predictions,
    refresh_all_predictions
)
from app.services.matching_algorithm_service import run_optimal_matching
from sqlalchemy.orm import Session
from sqlalchemy import func

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/matching", tags=["matching"])


# Student endpoints

@router.get("/students", response_model=StudentListPaginatedResponse)
async def get_students_endpoint(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Get list of all students with pagination."""
    try:
        students = db.query(Student).offset(offset).limit(limit).all()
        total = db.query(func.count(Student.id)).scalar()
        
        student_responses = [
            StudentListResponse(
                id=student.id,
                name=student.name,
                age=student.age,
                preferred_pace=student.preferred_pace,
                preferred_teaching_style=student.preferred_teaching_style
            )
            for student in students
        ]
        
        return StudentListPaginatedResponse(
            students=student_responses,
            total=total,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(f"Error fetching students: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch students"
        )


@router.get("/students/{student_id}", response_model=StudentResponse)
async def get_student_endpoint(
    student_id: UUID = Path(..., description="Student ID"),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Get student details by ID."""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found"
        )
    return student


@router.post("/students", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_student_endpoint(
    student_data: StudentCreate,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Create a new student."""
    try:
        student = Student(**student_data.model_dump())
        db.add(student)
        db.commit()
        db.refresh(student)
        return student
    except Exception as e:
        logger.error(f"Error creating student: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create student"
        )


# Tutor endpoints (with preferences)

@router.get("/tutors", response_model=list)
async def get_tutors_endpoint(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Get list of tutors with matching preferences."""
    try:
        tutors = db.query(Tutor).offset(offset).limit(limit).all()
        
        tutor_responses = []
        for tutor in tutors:
            tutor_dict = {
                'id': tutor.id,
                'name': tutor.name,
                'email': tutor.email,
                'age': tutor.age,
                'sex': tutor.sex,
                'experience_years': tutor.experience_years,
                'teaching_style': tutor.teaching_style,
                'preferred_pace': tutor.preferred_pace,
                'communication_style': tutor.communication_style,
                'confidence_level': tutor.confidence_level,
                'preferred_student_level': tutor.preferred_student_level,
            }
            tutor_responses.append(tutor_dict)
        
        return tutor_responses
    except Exception as e:
        logger.error(f"Error fetching tutors: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch tutors"
        )


@router.get("/tutors/{tutor_id}", response_model=dict)
async def get_tutor_endpoint(
    tutor_id: UUID = Path(..., description="Tutor ID"),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Get tutor details with preferences by ID."""
    tutor = db.query(Tutor).filter(Tutor.id == tutor_id).first()
    if not tutor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tutor with ID {tutor_id} not found"
        )
    
    return {
        'id': tutor.id,
        'name': tutor.name,
        'email': tutor.email,
        'age': tutor.age,
        'sex': tutor.sex,
        'experience_years': tutor.experience_years,
        'teaching_style': tutor.teaching_style,
        'preferred_pace': tutor.preferred_pace,
        'communication_style': tutor.communication_style,
        'confidence_level': tutor.confidence_level,
        'preferred_student_level': tutor.preferred_student_level,
        'preferences_json': tutor.preferences_json,
    }


@router.patch("/tutors/{tutor_id}", response_model=dict)
async def update_tutor_endpoint(
    tutor_id: UUID = Path(..., description="Tutor ID"),
    tutor_data: dict = Body(default={}, description="Tutor preferences to update"),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Update tutor preferences (partial update)."""
    tutor = db.query(Tutor).filter(Tutor.id == tutor_id).first()
    if not tutor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tutor with ID {tutor_id} not found"
        )
    
    # Update only provided fields
    if tutor_data:
        for key, value in tutor_data.items():
            if hasattr(tutor, key):
                setattr(tutor, key, value)
    
    db.commit()
    db.refresh(tutor)
    
    # Refresh match predictions for this tutor since data changed
    try:
        refreshed_count = refresh_tutor_predictions(db, str(tutor.id))
        logger.info(f"Refreshed {refreshed_count} match predictions after tutor update")
    except Exception as e:
        logger.warning(f"Failed to refresh match predictions after tutor update: {e}")
        # Don't fail the request if refresh fails
    
    return {
        'id': tutor.id,
        'name': tutor.name,
        'email': tutor.email,
        'age': tutor.age,
        'sex': tutor.sex,
        'experience_years': tutor.experience_years,
        'teaching_style': tutor.teaching_style,
        'preferred_pace': tutor.preferred_pace,
        'communication_style': tutor.communication_style,
        'confidence_level': tutor.confidence_level,
        'preferred_student_level': tutor.preferred_student_level,
        'preferences_json': tutor.preferences_json,
    }


# Match prediction endpoints

@router.get("/predict/{student_id}/{tutor_id}", response_model=MatchPredictionResponse)
async def get_match_prediction_endpoint(
    student_id: UUID = Path(..., description="Student ID"),
    tutor_id: UUID = Path(..., description="Tutor ID"),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Get or create match prediction for a student-tutor pair."""
    # Get student and tutor
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found"
        )
    
    tutor = db.query(Tutor).filter(Tutor.id == tutor_id).first()
    if not tutor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tutor with ID {tutor_id} not found"
        )
    
    # Get tutor stats
    tutor_stats = None
    if tutor.tutor_score:
        tutor_stats = {
            'reschedule_rate_30d': float(tutor.tutor_score.reschedule_rate_30d or 0),
            'total_sessions_30d': tutor.tutor_score.total_sessions_30d,
            'is_high_risk': tutor.tutor_score.is_high_risk,
        }
    
    # Get or create prediction
    try:
        match_prediction = get_or_create_match_prediction(
            db, student, tutor, tutor_stats
        )
        return match_prediction
    except Exception as e:
        logger.error(f"Error creating match prediction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create match prediction: {str(e)}"
        )


@router.post("/generate-all")
async def generate_all_predictions_endpoint(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Generate match predictions for all student-tutor pairs."""
    try:
        students = db.query(Student).all()
        tutors = db.query(Tutor).all()
        
        if not students:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No students found. Create students first."
            )
        
        if not tutors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No tutors found."
            )
        
        created_count = 0
        existing_count = 0
        
        for student in students:
            for tutor in tutors:
                # Check if prediction exists
                existing = db.query(MatchPrediction).filter(
                    MatchPrediction.student_id == student.id,
                    MatchPrediction.tutor_id == tutor.id
                ).first()
                
                if existing:
                    existing_count += 1
                    continue
                
                # Get tutor stats
                tutor_stats = None
                if tutor.tutor_score:
                    tutor_stats = {
                        'reschedule_rate_30d': float(tutor.tutor_score.reschedule_rate_30d or 0),
                        'total_sessions_30d': tutor.tutor_score.total_sessions_30d,
                        'is_high_risk': tutor.tutor_score.is_high_risk,
                    }
                
                # Create prediction
                match_prediction = get_or_create_match_prediction(
                    db, student, tutor, tutor_stats
                )
                created_count += 1
        
        return {
            'message': 'Predictions generated successfully',
            'created': created_count,
            'existing': existing_count,
            'total': created_count + existing_count
        }
    except Exception as e:
        logger.error(f"Error generating predictions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate predictions: {str(e)}"
        )


@router.post("/refresh-all")
async def refresh_all_predictions_endpoint(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Refresh all match predictions in the database.
    
    This endpoint recalculates all existing match predictions with updated data.
    Use this when:
    - Tutor scores/churn data has been updated
    - Student or tutor preferences have changed
    - Model has been retrained
    """
    try:
        total_refreshed = refresh_all_predictions(db)
        return {
            'message': 'All predictions refreshed successfully',
            'total_refreshed': total_refreshed
        }
    except Exception as e:
        logger.error(f"Error refreshing predictions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh predictions: {str(e)}"
        )


@router.post("/refresh-tutor/{tutor_id}")
async def refresh_tutor_predictions_endpoint(
    tutor_id: UUID = Path(..., description="Tutor ID"),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Refresh all match predictions for a specific tutor.
    
    This should be called when tutor data or tutor_stats change.
    """
    try:
        refreshed_count = refresh_tutor_predictions(db, str(tutor_id))
        return {
            'message': f'Predictions refreshed for tutor {tutor_id}',
            'refreshed_count': refreshed_count
        }
    except Exception as e:
        logger.error(f"Error refreshing tutor predictions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh tutor predictions: {str(e)}"
        )


@router.post("/refresh-student/{student_id}")
async def refresh_student_predictions_endpoint(
    student_id: UUID = Path(..., description="Student ID"),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Refresh all match predictions for a specific student.
    
    This should be called when student data changes.
    """
    try:
        refreshed_count = refresh_student_predictions(db, str(student_id))
        return {
            'message': f'Predictions refreshed for student {student_id}',
            'refreshed_count': refreshed_count
        }
    except Exception as e:
        logger.error(f"Error refreshing student predictions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh student predictions: {str(e)}"
        )


@router.get("/students/{student_id}/matches", response_model=MatchPredictionListResponse)
async def get_student_matches_endpoint(
    student_id: UUID = Path(..., description="Student ID"),
    sort_by: Optional[str] = Query("compatibility_score", description="Sort field: compatibility_score, churn_probability, risk_level"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc, desc"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Get all match predictions for a student."""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found"
        )
    
    # Build query
    query = db.query(MatchPrediction).filter(
        MatchPrediction.student_id == student_id
    )
    
    # Apply sorting
    if sort_by == "compatibility_score":
        order_by = MatchPrediction.compatibility_score.desc() if sort_order == "desc" else MatchPrediction.compatibility_score.asc()
    elif sort_by == "churn_probability":
        order_by = MatchPrediction.churn_probability.desc() if sort_order == "desc" else MatchPrediction.churn_probability.asc()
    elif sort_by == "risk_level":
        order_by = MatchPrediction.risk_level.desc() if sort_order == "desc" else MatchPrediction.risk_level.asc()
    else:
        order_by = MatchPrediction.compatibility_score.desc()
    
    query = query.order_by(order_by)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    predictions = query.offset(offset).limit(limit).all()
    
    # Build response with details
    matches = []
    for prediction in predictions:
        tutor = db.query(Tutor).filter(Tutor.id == prediction.tutor_id).first()
        if tutor:
            matches.append(MatchPredictionWithDetails(
                **prediction.__dict__,
                student=StudentListResponse(
                    id=student.id,
                    name=student.name,
                    age=student.age,
                    preferred_pace=student.preferred_pace,
                    preferred_teaching_style=student.preferred_teaching_style
                ),
                tutor=TutorListResponse(
                    id=tutor.id,
                    name=tutor.name,
                    reschedule_rate_30d=None,
                    is_high_risk=False,
                    total_sessions_30d=0,
                    tutor_reschedules_30d=0,
                    last_calculated_at=None
                )
            ))
    
    return MatchPredictionListResponse(
        matches=matches,
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/tutors/{tutor_id}/matches", response_model=MatchPredictionListResponse)
async def get_tutor_matches_endpoint(
    tutor_id: UUID = Path(..., description="Tutor ID"),
    sort_by: Optional[str] = Query("compatibility_score", description="Sort field: compatibility_score, churn_probability, risk_level"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc, desc"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """Get all match predictions for a tutor."""
    tutor = db.query(Tutor).filter(Tutor.id == tutor_id).first()
    if not tutor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tutor with ID {tutor_id} not found"
        )
    
    # Build query
    query = db.query(MatchPrediction).filter(
        MatchPrediction.tutor_id == tutor_id
    )
    
    # Apply sorting (similar to student matches)
    if sort_by == "compatibility_score":
        order_by = MatchPrediction.compatibility_score.desc() if sort_order == "desc" else MatchPrediction.compatibility_score.asc()
    elif sort_by == "churn_probability":
        order_by = MatchPrediction.churn_probability.desc() if sort_order == "desc" else MatchPrediction.churn_probability.asc()
    elif sort_by == "risk_level":
        order_by = MatchPrediction.risk_level.desc() if sort_order == "desc" else MatchPrediction.risk_level.asc()
    else:
        order_by = MatchPrediction.compatibility_score.desc()
    
    query = query.order_by(order_by)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    predictions = query.offset(offset).limit(limit).all()
    
    # Build response with details
    matches = []
    for prediction in predictions:
        student = db.query(Student).filter(Student.id == prediction.student_id).first()
        if student:
            matches.append(MatchPredictionWithDetails(
                **prediction.__dict__,
                student=StudentListResponse(
                    id=student.id,
                    name=student.name,
                    age=student.age,
                    preferred_pace=student.preferred_pace,
                    preferred_teaching_style=student.preferred_teaching_style
                ),
                tutor=TutorListResponse(
                    id=tutor.id,
                    name=tutor.name,
                    reschedule_rate_30d=None,
                    is_high_risk=False,
                    total_sessions_30d=0,
                    tutor_reschedules_30d=0,
                    last_calculated_at=None
                )
            ))
    
    return MatchPredictionListResponse(
        matches=matches,
        total=total,
        limit=limit,
        offset=offset
    )


# Matching algorithm endpoints

class RunMatchingRequest(BaseModel):
    """Request schema for running matching algorithm."""
    student_ids: List[UUID] = Field(..., min_length=2, description="List of student UUIDs")
    tutor_ids: List[UUID] = Field(..., min_length=2, description="List of tutor UUIDs")


class MatchingResult(BaseModel):
    """Schema for a single match result."""
    student_id: UUID
    tutor_id: UUID
    churn_probability: float = Field(..., ge=0, le=1, description="Churn probability (0-1)")
    compatibility_score: float = Field(..., ge=0, le=1, description="Compatibility score (0-1)")
    risk_level: str = Field(..., description="Risk level ('low', 'medium', 'high')")
    pace_mismatch: float = Field(..., ge=0, description="Pace mismatch score")
    style_mismatch: float = Field(..., ge=0, description="Teaching style mismatch score")
    communication_mismatch: float = Field(..., ge=0, description="Communication mismatch score")
    age_difference: int = Field(..., ge=0, description="Age difference in years")


class RunMatchingResponse(BaseModel):
    """Response schema for matching algorithm results."""
    matches: List[MatchingResult]
    total_churn_risk: float = Field(..., description="Sum of all churn probabilities")
    avg_churn_risk: float = Field(..., description="Average churn probability")
    total_compatibility: float = Field(..., description="Sum of all compatibility scores")
    avg_compatibility: float = Field(..., description="Average compatibility score")


@router.post("/run-matching", response_model=RunMatchingResponse)
async def run_matching_endpoint(
    request: RunMatchingRequest = Body(..., description="Matching request with student and tutor IDs"),
    db: Session = Depends(get_db),
    _: bool = Depends(verify_api_key)
):
    """
    Run optimal matching algorithm to find 1-to-1 assignments with minimal churn risk.
    
    Uses Hungarian algorithm to find optimal assignment that minimizes total churn probability.
    Requires equal number of students and tutors.
    """
    try:
        logger.info(f"Run matching request: {len(request.student_ids)} students, {len(request.tutor_ids)} tutors")
        
        # Validate equal counts
        if len(request.student_ids) != len(request.tutor_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Student and tutor lists must be equal length. "
                       f"Got {len(request.student_ids)} students and {len(request.tutor_ids)} tutors."
            )
        
        # Validate minimum count
        if len(request.student_ids) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least 2 students and tutors are required for matching."
            )
        
        # Validate all IDs exist
        existing_students = db.query(Student).filter(Student.id.in_(request.student_ids)).all()
        existing_tutors = db.query(Tutor).filter(Tutor.id.in_(request.tutor_ids)).all()
        
        if len(existing_students) != len(request.student_ids):
            found_ids = {s.id for s in existing_students}
            missing = set(request.student_ids) - found_ids
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Students not found: {list(missing)}"
            )
        
        if len(existing_tutors) != len(request.tutor_ids):
            found_ids = {t.id for t in existing_tutors}
            missing = set(request.tutor_ids) - found_ids
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tutors not found: {list(missing)}"
            )
        
        # Run matching algorithm
        logger.info("Running optimal matching algorithm...")
        result = run_optimal_matching(db, request.student_ids, request.tutor_ids)
        logger.info(f"Matching algorithm completed: {len(result['matches'])} matches")
        
        # Convert to response format
        matches = [
            MatchingResult(**match) for match in result['matches']
        ]
        
        response = RunMatchingResponse(
            matches=matches,
            total_churn_risk=result['total_churn_risk'],
            avg_churn_risk=result['avg_churn_risk'],
            total_compatibility=result['total_compatibility'],
            avg_compatibility=result['avg_compatibility'],
        )
        logger.info(f"Returning response with {len(matches)} matches")
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ImportError as e:
        logger.error(f"Scipy not available: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Matching algorithm not available. Please install scipy: pip install scipy"
        )
    except Exception as e:
        logger.error(f"Error running matching algorithm: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run matching algorithm: {str(e)}"
        )

