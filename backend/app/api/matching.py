"""
Matching service API endpoints.
"""
from fastapi import APIRouter, HTTPException, Query, Depends, Path, Body, status
from typing import Optional
from uuid import UUID
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
from app.services.match_prediction_service import get_or_create_match_prediction
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating predictions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate predictions: {str(e)}"
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

