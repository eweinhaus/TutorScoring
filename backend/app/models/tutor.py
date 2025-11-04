"""
Tutor model representing tutor profiles.
"""
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Column, String, Boolean, Index
from sqlalchemy.orm import relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.session import Session
    from app.models.tutor_score import TutorScore


class Tutor(BaseModel):
    """
    Tutor model representing a tutor profile.
    
    Relationships:
    - sessions: One-to-many relationship with Session model
    - tutor_score: One-to-one relationship with TutorScore model
    """
    __tablename__ = 'tutors'
    
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    sessions = relationship(
        'Session',
        back_populates='tutor',
        cascade='all, delete-orphan'
    )
    tutor_score = relationship(
        'TutorScore',
        back_populates='tutor',
        uselist=False
    )
    
    # Indexes
    __table_args__ = (
        Index('ix_tutors_email', 'email'),
        Index('ix_tutors_created_at', 'created_at'),
    )
    
    def get_reschedule_rate(self, days: int) -> Optional[float]:
        """
        Calculate reschedule rate for a given time window.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Reschedule rate as a percentage (0-100), or None if no sessions
        """
        from datetime import datetime, timedelta
        from sqlalchemy import and_, func
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        total_sessions = len([
            s for s in self.sessions
            if s.scheduled_time >= cutoff_date
        ])
        
        if total_sessions == 0:
            return None
        
        tutor_reschedules = len([
            s for s in self.sessions
            if s.scheduled_time >= cutoff_date
            and s.status == 'rescheduled'
            and s.reschedule
            and s.reschedule.initiator == 'tutor'
        ])
        
        return (tutor_reschedules / total_sessions) * 100 if total_sessions > 0 else 0.0
    
    def calculate_risk_score(self) -> Optional[str]:
        """
        Determine risk level based on tutor_score if available.
        
        Returns:
            Risk level string ('low', 'medium', 'high') or None
        """
        if not self.tutor_score:
            return None
        
        rates = [
            self.tutor_score.reschedule_rate_7d or 0,
            self.tutor_score.reschedule_rate_30d or 0,
            self.tutor_score.reschedule_rate_90d or 0
        ]
        
        max_rate = max(rates) if rates else 0
        
        if max_rate >= 20:
            return 'high'
        elif max_rate >= 10:
            return 'medium'
        else:
            return 'low'
    
    def __repr__(self) -> str:
        return f"<Tutor(id={self.id}, name='{self.name}', email='{self.email}', is_active={self.is_active})>"

