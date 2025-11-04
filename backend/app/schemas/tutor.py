"""
Pydantic schemas for Tutor model.
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator
from uuid import UUID
import re


class TutorBase(BaseModel):
    """Base schema for Tutor."""
    name: str = Field(..., min_length=1, max_length=255, description="Tutor full name")
    email: Optional[str] = Field(None, max_length=255, description="Tutor email address")
    is_active: bool = Field(True, description="Whether tutor is active")
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        """Validate email format if provided."""
        if v is not None and not re.match(r'^[^@]+@[^@]+\.[^@]+$', v):
            raise ValueError('Invalid email format')
        return v


class TutorCreate(TutorBase):
    """Schema for creating a new tutor."""
    pass


class TutorResponse(TutorBase):
    """Schema for tutor API responses."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class TutorWithScores(TutorResponse):
    """Schema for tutor with calculated scores."""
    reschedule_rate_7d: Optional[float] = None
    reschedule_rate_30d: Optional[float] = None
    reschedule_rate_90d: Optional[float] = None
    is_high_risk: bool = False
    
    model_config = ConfigDict(from_attributes=True)


class TutorListResponse(BaseModel):
    """Schema for tutor list API responses."""
    id: UUID
    name: str
    reschedule_rate_30d: Optional[float] = None
    is_high_risk: bool = False
    total_sessions_30d: int = 0
    tutor_reschedules_30d: int = 0
    last_calculated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class TutorDetailResponse(BaseModel):
    """Schema for tutor detail API responses."""
    id: UUID
    name: str
    email: Optional[str] = None
    created_at: datetime
    scores: 'TutorScoreResponse'
    statistics: dict  # Same as scores but different name for clarity
    
    model_config = ConfigDict(from_attributes=True)


class TutorListPaginatedResponse(BaseModel):
    """Schema for paginated tutor list responses."""
    tutors: list[TutorListResponse]
    total: int
    limit: int
    offset: int


class TutorHistoryResponse(BaseModel):
    """Schema for tutor history API responses."""
    reschedules: list['RescheduleResponse']
    trend: dict  # Contains reschedule_rate_by_week data
    
    model_config = ConfigDict(from_attributes=True)


# Forward references
from app.schemas.tutor_score import TutorScoreResponse
from app.schemas.reschedule import RescheduleResponse
TutorDetailResponse.model_rebuild()
TutorHistoryResponse.model_rebuild()

