"""
Pydantic schemas for MatchPrediction model.
"""
from typing import Optional
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID


class MatchPredictionBase(BaseModel):
    """Base schema for MatchPrediction."""
    churn_probability: Decimal = Field(..., ge=0, le=1, description="Churn probability (0-1)")
    risk_level: str = Field(..., description="Risk level ('low', 'medium', 'high')")
    compatibility_score: Decimal = Field(..., ge=0, le=1, description="Compatibility score (0-1)")
    pace_mismatch: Decimal = Field(..., ge=0, description="Pace mismatch score")
    style_mismatch: Decimal = Field(..., ge=0, description="Teaching style mismatch score")
    communication_mismatch: Decimal = Field(..., ge=0, description="Communication mismatch score")
    age_difference: int = Field(..., ge=0, description="Age difference in years")
    ai_explanation: Optional[str] = Field(None, description="AI-generated explanation")
    model_version: Optional[str] = Field(None, description="Model version")


class MatchPredictionResponse(MatchPredictionBase):
    """Schema for match prediction API responses."""
    id: UUID
    student_id: UUID
    tutor_id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class MatchPredictionWithDetails(MatchPredictionResponse):
    """Schema for match prediction with student and tutor details."""
    student: 'StudentListResponse'
    tutor: 'TutorListResponse'
    
    model_config = ConfigDict(from_attributes=True)


class MatchPredictionListResponse(BaseModel):
    """Schema for match prediction list responses."""
    matches: list[MatchPredictionWithDetails]
    total: int
    limit: int
    offset: int


# Forward references
from app.schemas.student import StudentListResponse
from app.schemas.tutor import TutorListResponse
MatchPredictionWithDetails.model_rebuild()

