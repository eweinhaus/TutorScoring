"""
Pydantic schemas for TutorScore model.
"""
from typing import Optional
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID


class TutorScoreResponse(BaseModel):
    """Schema for tutor score API responses."""
    id: UUID
    tutor_id: UUID
    reschedule_rate_7d: Optional[Decimal] = Field(None, ge=0, le=100, description="7-day reschedule rate percentage")
    reschedule_rate_30d: Optional[Decimal] = Field(None, ge=0, le=100, description="30-day reschedule rate percentage")
    reschedule_rate_90d: Optional[Decimal] = Field(None, ge=0, le=100, description="90-day reschedule rate percentage")
    total_sessions_7d: int = Field(0, ge=0, description="Total sessions in 7 days")
    total_sessions_30d: int = Field(0, ge=0, description="Total sessions in 30 days")
    total_sessions_90d: int = Field(0, ge=0, description="Total sessions in 90 days")
    tutor_reschedules_7d: int = Field(0, ge=0, description="Tutor-initiated reschedules in 7 days")
    tutor_reschedules_30d: int = Field(0, ge=0, description="Tutor-initiated reschedules in 30 days")
    tutor_reschedules_90d: int = Field(0, ge=0, description="Tutor-initiated reschedules in 90 days")
    is_high_risk: bool = Field(False, description="Risk flag (exceeds threshold)")
    risk_threshold: Decimal = Field(15.00, description="Threshold used for flagging")
    last_calculated_at: datetime
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

