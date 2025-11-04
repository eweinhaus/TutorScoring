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

