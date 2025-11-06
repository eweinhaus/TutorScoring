"""
SQLAlchemy model for session reschedule predictions.
"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class SessionReschedulePrediction(BaseModel):
    """
    Session reschedule prediction model.
    Stores ML predictions for likelihood of tutor rescheduling.
    """
    __tablename__ = "session_reschedule_predictions"
    
    # Foreign key to session
    session_id = Column(UUID(as_uuid=True), ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False, unique=True)
    
    # Prediction results
    reschedule_probability = Column(Float, nullable=False, doc="Probability of reschedule (0-1)")
    risk_level = Column(String(20), nullable=False, doc="Risk level: low, medium, high")
    
    # Model metadata
    model_version = Column(String(50), nullable=False, default="v1.0", doc="Version of ML model used")
    predicted_at = Column(DateTime, nullable=False, default=datetime.utcnow, doc="When prediction was made")
    
    # Features used for prediction (JSON for flexibility)
    features_json = Column(JSON, nullable=True, doc="Features used for prediction")
    
    # Relationships
    session = relationship("Session", back_populates="reschedule_prediction")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('reschedule_probability >= 0 AND reschedule_probability <= 1', name='valid_probability'),
        CheckConstraint("risk_level IN ('low', 'medium', 'high')", name='valid_risk_level'),
        Index('idx_session_reschedule_predictions_session_id', 'session_id'),
        Index('idx_session_reschedule_predictions_risk_level', 'risk_level'),
        Index('idx_session_reschedule_predictions_predicted_at', 'predicted_at'),
    )
    
    def __repr__(self):
        return f"<SessionReschedulePrediction(session_id={self.session_id}, probability={self.reschedule_probability}, risk={self.risk_level})>"
