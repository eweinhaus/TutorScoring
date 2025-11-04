"""
TutorScore model representing calculated risk scores for tutors.
"""
from typing import TYPE_CHECKING, Dict, Optional
from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey, Numeric, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.tutor import Tutor


class TutorScore(BaseModel):
    """
    TutorScore model storing calculated risk scores and flags for tutors.
    
    Relationships:
    - tutor: One-to-one relationship with Tutor model
    
    Constraints:
    - Reschedule rates must be between 0 and 100
    - is_high_risk should be true if any rate > risk_threshold
    """
    __tablename__ = 'tutor_scores'
    
    tutor_id = Column(UUID(as_uuid=True), ForeignKey('tutors.id'), unique=True, nullable=False)
    reschedule_rate_7d = Column(Numeric(5, 2), nullable=True)
    reschedule_rate_30d = Column(Numeric(5, 2), nullable=True)
    reschedule_rate_90d = Column(Numeric(5, 2), nullable=True)
    total_sessions_7d = Column(Integer, default=0, nullable=False)
    total_sessions_30d = Column(Integer, default=0, nullable=False)
    total_sessions_90d = Column(Integer, default=0, nullable=False)
    tutor_reschedules_7d = Column(Integer, default=0, nullable=False)
    tutor_reschedules_30d = Column(Integer, default=0, nullable=False)
    tutor_reschedules_90d = Column(Integer, default=0, nullable=False)
    is_high_risk = Column(Boolean, default=False, nullable=False)
    risk_threshold = Column(Numeric(5, 2), default=15.00, nullable=False)
    last_calculated_at = Column(DateTime, nullable=False)
    
    # Relationships
    tutor = relationship('Tutor', back_populates='tutor_score')
    
    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint(
            "reschedule_rate_7d IS NULL OR (reschedule_rate_7d >= 0 AND reschedule_rate_7d <= 100)",
            name='check_rate_7d'
        ),
        CheckConstraint(
            "reschedule_rate_30d IS NULL OR (reschedule_rate_30d >= 0 AND reschedule_rate_30d <= 100)",
            name='check_rate_30d'
        ),
        CheckConstraint(
            "reschedule_rate_90d IS NULL OR (reschedule_rate_90d >= 0 AND reschedule_rate_90d <= 100)",
            name='check_rate_90d'
        ),
        # Note: is_high_risk constraint is complex and may need application-level enforcement
        # The constraint below is a simplified version
        CheckConstraint(
            "(is_high_risk = false) OR (reschedule_rate_7d > risk_threshold OR reschedule_rate_30d > risk_threshold OR reschedule_rate_90d > risk_threshold)",
            name='check_risk_flag'
        ),
        Index('ix_tutor_scores_tutor_id', 'tutor_id'),
        Index('ix_tutor_scores_is_high_risk', 'is_high_risk'),
        Index('ix_tutor_scores_last_calculated_at', 'last_calculated_at'),
    )
    
    def update_rates(self, rates_7d: Optional[float], rates_30d: Optional[float], rates_90d: Optional[float],
                     counts_7d: int, counts_30d: int, counts_90d: int,
                     reschedules_7d: int, reschedules_30d: int, reschedules_90d: int) -> None:
        """
        Update all reschedule rates and counts.
        
        Args:
            rates_7d: 7-day reschedule rate
            rates_30d: 30-day reschedule rate
            rates_90d: 90-day reschedule rate
            counts_7d: Total sessions in 7 days
            counts_30d: Total sessions in 30 days
            counts_90d: Total sessions in 90 days
            reschedules_7d: Tutor-initiated reschedules in 7 days
            reschedules_30d: Tutor-initiated reschedules in 30 days
            reschedules_90d: Tutor-initiated reschedules in 90 days
        """
        from datetime import datetime
        
        self.reschedule_rate_7d = rates_7d
        self.reschedule_rate_30d = rates_30d
        self.reschedule_rate_90d = rates_90d
        self.total_sessions_7d = counts_7d
        self.total_sessions_30d = counts_30d
        self.total_sessions_90d = counts_90d
        self.tutor_reschedules_7d = reschedules_7d
        self.tutor_reschedules_30d = reschedules_30d
        self.tutor_reschedules_90d = reschedules_90d
        self.last_calculated_at = datetime.utcnow()
        self.check_risk_flag()
    
    def check_risk_flag(self) -> None:
        """
        Update is_high_risk flag based on reschedule rates and threshold.
        """
        rates = [
            self.reschedule_rate_7d or 0,
            self.reschedule_rate_30d or 0,
            self.reschedule_rate_90d or 0
        ]
        
        threshold = float(self.risk_threshold)
        self.is_high_risk = any(float(rate or 0) > threshold for rate in rates)
    
    def to_dict(self) -> Dict:
        """
        Convert TutorScore to dictionary for API responses.
        
        Returns:
            Dictionary representation of TutorScore
        """
        return {
            'id': str(self.id),
            'tutor_id': str(self.tutor_id),
            'reschedule_rate_7d': float(self.reschedule_rate_7d) if self.reschedule_rate_7d else None,
            'reschedule_rate_30d': float(self.reschedule_rate_30d) if self.reschedule_rate_30d else None,
            'reschedule_rate_90d': float(self.reschedule_rate_90d) if self.reschedule_rate_90d else None,
            'total_sessions_7d': self.total_sessions_7d,
            'total_sessions_30d': self.total_sessions_30d,
            'total_sessions_90d': self.total_sessions_90d,
            'tutor_reschedules_7d': self.tutor_reschedules_7d,
            'tutor_reschedules_30d': self.tutor_reschedules_30d,
            'tutor_reschedules_90d': self.tutor_reschedules_90d,
            'is_high_risk': self.is_high_risk,
            'risk_threshold': float(self.risk_threshold),
            'last_calculated_at': self.last_calculated_at.isoformat() if self.last_calculated_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self) -> str:
        return f"<TutorScore(id={self.id}, tutor_id={self.tutor_id}, is_high_risk={self.is_high_risk})>"

