"""
Pydantic schemas for SessionReschedulePrediction model.
"""
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, field_validator
from uuid import UUID


class SessionReschedulePredictionBase(BaseModel):
    """Base schema for SessionReschedulePrediction."""
    reschedule_probability: Decimal = Field(..., ge=0, le=1, description="Reschedule probability (0-1)")
    risk_level: str = Field(..., description="Risk level ('low', 'medium', 'high')")
    model_version: str = Field(default='v1.0', description="Model version")
    predicted_at: datetime = Field(default_factory=datetime.utcnow, description="When prediction was made")
    features_json: Optional[Dict[str, Any]] = Field(None, description="Feature values for debugging")
    
    @field_validator('risk_level')
    @classmethod
    def validate_risk_level(cls, v: str) -> str:
        """Validate risk level is one of the allowed values."""
        allowed_values = ['low', 'medium', 'high']
        if v not in allowed_values:
            raise ValueError(f"risk_level must be one of {allowed_values}, got {v}")
        return v


class SessionReschedulePredictionCreate(SessionReschedulePredictionBase):
    """Schema for creating a session reschedule prediction."""
    session_id: UUID = Field(..., description="Session ID")


class SessionReschedulePredictionResponse(SessionReschedulePredictionBase):
    """Schema for session reschedule prediction API responses."""
    id: UUID
    session_id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class SessionReschedulePredictionWithSession(SessionReschedulePredictionResponse):
    """Schema for session reschedule prediction with session details."""
    session: 'SessionResponse'
    
    model_config = ConfigDict(from_attributes=True)


# Forward references
from app.schemas.session import SessionResponse
SessionReschedulePredictionWithSession.model_rebuild()

