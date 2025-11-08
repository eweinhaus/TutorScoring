"""
Pydantic schemas for session reschedule predictions.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


class SessionReschedulePredictionBase(BaseModel):
    """Base schema for session reschedule predictions."""
    session_id: UUID
    reschedule_probability: float = Field(..., ge=0.0, le=1.0, description="Probability of reschedule (0-1)")
    risk_level: str = Field(..., description="Risk level: low, medium, high")
    model_version: str = Field(default="v1.0", description="Version of ML model used")
    features_json: Optional[Dict[str, Any]] = Field(default=None, description="Features used for prediction")


class SessionReschedulePredictionCreate(SessionReschedulePredictionBase):
    """Schema for creating a new session reschedule prediction."""
    pass


class SessionReschedulePredictionResponse(SessionReschedulePredictionBase):
    """Schema for session reschedule prediction responses."""
    id: UUID
    predicted_at: datetime
    
    class Config:
        from_attributes = True
