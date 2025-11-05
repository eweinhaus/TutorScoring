"""
Pydantic schemas for Student model.
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator
from uuid import UUID


class StudentBase(BaseModel):
    """Base schema for Student."""
    name: str = Field(..., min_length=1, max_length=255, description="Student full name")
    age: int = Field(..., ge=8, le=25, description="Student age (8-25)")
    sex: Optional[str] = Field(None, max_length=10, description="Student sex ('male', 'female', 'other', or None)")
    preferred_pace: int = Field(..., ge=1, le=5, description="Preferred pace (1=slow, 5=fast)")
    preferred_teaching_style: str = Field(..., max_length=50, description="Preferred teaching style")
    communication_style_preference: int = Field(..., ge=1, le=5, description="Communication style (1=formal, 5=casual)")
    urgency_level: int = Field(..., ge=1, le=5, description="Urgency level (1=low, 5=high)")
    learning_goals: Optional[str] = Field(None, max_length=500, description="Learning goals")
    previous_tutoring_experience: int = Field(0, ge=0, description="Number of previous tutoring sessions")
    previous_satisfaction: Optional[int] = Field(None, ge=1, le=5, description="Previous satisfaction (1=very dissatisfied, 5=very satisfied)")
    preferences_json: Optional[Dict[str, Any]] = Field(None, description="Additional flexible preferences")
    
    @field_validator('sex')
    @classmethod
    def validate_sex(cls, v):
        """Validate sex value if provided."""
        if v is not None and v not in ['male', 'female', 'other']:
            raise ValueError('Sex must be "male", "female", "other", or None')
        return v
    
    @field_validator('preferred_teaching_style')
    @classmethod
    def validate_teaching_style(cls, v):
        """Validate teaching style."""
        valid_styles = ['structured', 'flexible', 'interactive', 'traditional', 'modern']
        if v.lower() not in valid_styles:
            # Allow any string but suggest valid ones
            pass
        return v


class StudentCreate(StudentBase):
    """Schema for creating a new student."""
    pass


class StudentResponse(StudentBase):
    """Schema for student API responses."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class StudentListResponse(BaseModel):
    """Schema for student list API responses (lightweight)."""
    id: UUID
    name: str
    age: int
    preferred_pace: int
    preferred_teaching_style: str
    
    model_config = ConfigDict(from_attributes=True)


class StudentListPaginatedResponse(BaseModel):
    """Schema for paginated student list responses."""
    students: list[StudentListResponse]
    total: int
    limit: int
    offset: int

