"""
Pydantic schemas for Session model.
"""
from typing import Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID

from app.schemas.reschedule import RescheduleInfo


class SessionBase(BaseModel):
    """Base schema for Session."""
    tutor_id: UUID = Field(..., description="Tutor ID")
    student_id: str = Field(..., min_length=1, max_length=255, description="Student identifier")
    scheduled_time: datetime = Field(..., description="Scheduled session time")
    status: Literal['completed', 'rescheduled', 'no_show'] = Field(..., description="Session status")


class SessionCreate(SessionBase):
    """Schema for creating a new session."""
    completed_time: Optional[datetime] = Field(None, description="Actual completion time")
    duration_minutes: Optional[int] = Field(None, ge=1, le=300, description="Session duration in minutes")
    reschedule_info: Optional[RescheduleInfo] = Field(None, description="Reschedule information if applicable")


class SessionResponse(SessionBase):
    """Schema for session API responses."""
    id: UUID
    completed_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class SessionWithDetails(SessionResponse):
    """Schema for session with related data."""
    tutor_name: Optional[str] = None
    reschedule: Optional['RescheduleResponse'] = None  # Forward reference
    
    model_config = ConfigDict(from_attributes=True)


# Update forward references
from app.schemas.reschedule import RescheduleResponse
SessionWithDetails.model_rebuild()

