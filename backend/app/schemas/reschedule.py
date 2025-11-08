"""
Pydantic schemas for Reschedule model.
"""
from typing import Optional, Literal
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID


class RescheduleInfo(BaseModel):
    """Schema for reschedule information in session creation."""
    initiator: Literal['tutor', 'student'] = Field(..., description="Who initiated the reschedule")
    original_time: datetime = Field(..., description="Original scheduled time")
    new_time: Optional[datetime] = Field(None, description="New scheduled time (NULL if cancelled)")
    reason: Optional[str] = Field(None, description="Reschedule reason")
    reason_code: Optional[str] = Field(None, max_length=100, description="Categorized reason code")
    cancelled_at: datetime = Field(..., description="When reschedule was initiated")


class RescheduleResponse(BaseModel):
    """Schema for reschedule API responses."""
    id: UUID
    session_id: UUID
    initiator: Literal['tutor', 'student']
    original_time: datetime
    new_time: Optional[datetime] = None
    reason: Optional[str] = None
    reason_code: Optional[str] = None
    cancelled_at: datetime
    hours_before_session: Optional[Decimal] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

