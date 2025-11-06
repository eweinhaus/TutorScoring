"""
Session model representing tutoring sessions.
"""
from typing import TYPE_CHECKING, Optional
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.tutor import Tutor
    from app.models.reschedule import Reschedule
    from app.models.email_report import EmailReport
    from app.models.session_reschedule_prediction import SessionReschedulePrediction


class Session(BaseModel):
    """
    Session model representing a tutoring session.
    
    Relationships:
    - tutor: Many-to-one relationship with Tutor model
    - reschedule: One-to-one relationship with Reschedule model (optional)
    - email_report: One-to-one relationship with EmailReport model (optional)
    
    Constraints:
    - status must be 'completed', 'rescheduled', or 'no_show'
    - completed_time must be NULL if status is 'rescheduled' or 'no_show'
    - completed_time must be >= scheduled_time if not NULL
    """
    __tablename__ = 'sessions'
    
    tutor_id = Column(UUID(as_uuid=True), ForeignKey('tutors.id'), nullable=False)
    student_id = Column(String(255), nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    completed_time = Column(DateTime, nullable=True)
    status = Column(String(50), nullable=False)
    duration_minutes = Column(Integer, nullable=True)
    
    # Relationships
    tutor = relationship('Tutor', back_populates='sessions')
    reschedule = relationship(
        'Reschedule',
        back_populates='session',
        uselist=False,
        cascade='all, delete-orphan'
    )
    email_report = relationship(
        'EmailReport',
        back_populates='session',
        uselist=False,
        cascade='all, delete-orphan'
    )
    session_reschedule_prediction = relationship(
        'SessionReschedulePrediction',
        back_populates='session',
        uselist=False,
        cascade='all, delete-orphan'
    )
    
    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint(
            "status IN ('completed', 'rescheduled', 'no_show')",
            name='check_status'
        ),
        CheckConstraint(
            "(status IN ('rescheduled', 'no_show') AND completed_time IS NULL) OR (status = 'completed')",
            name='check_completed_time_null'
        ),
        CheckConstraint(
            "completed_time IS NULL OR completed_time >= scheduled_time",
            name='check_time_order'
        ),
        Index('ix_sessions_tutor_id', 'tutor_id'),
        Index('ix_sessions_scheduled_time', 'scheduled_time'),
        Index('ix_sessions_status', 'status'),
        Index('ix_sessions_tutor_scheduled', 'tutor_id', 'scheduled_time'),
    )
    
    def is_rescheduled(self) -> bool:
        """Check if session was rescheduled."""
        return self.status == 'rescheduled' and self.reschedule is not None
    
    def is_completed(self) -> bool:
        """Check if session was completed."""
        return self.status == 'completed' and self.completed_time is not None
    
    def get_duration(self) -> Optional[int]:
        """
        Get session duration in minutes.
        
        Returns:
            Duration in minutes if available, None otherwise
        """
        return self.duration_minutes
    
    def __repr__(self) -> str:
        return f"<Session(id={self.id}, tutor_id={self.tutor_id}, student_id='{self.student_id}', status='{self.status}')>"

