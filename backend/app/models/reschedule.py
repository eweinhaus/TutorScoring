"""
Reschedule model representing reschedule events.
"""
from typing import TYPE_CHECKING, Optional
from datetime import datetime, timedelta
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Numeric, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.session import Session


class Reschedule(BaseModel):
    """
    Reschedule model representing a reschedule event for a session.
    
    Note: This model does not have updated_at field per PRD specification.
    
    Relationships:
    - session: One-to-one relationship with Session model
    
    Constraints:
    - initiator must be 'tutor' or 'student'
    - new_time must be > original_time if not NULL
    """
    __tablename__ = 'reschedules'
    
    session_id = Column(UUID(as_uuid=True), ForeignKey('sessions.id'), unique=True, nullable=False)
    initiator = Column(String(50), nullable=False)
    original_time = Column(DateTime, nullable=False)
    new_time = Column(DateTime, nullable=True)
    reason = Column(Text, nullable=True)
    reason_code = Column(String(100), nullable=True)
    cancelled_at = Column(DateTime, nullable=False)
    hours_before_session = Column(Numeric(10, 2), nullable=True)
    
    # Note: No updated_at field per PRD specification
    # Override to exclude updated_at from this model
    @declared_attr
    def updated_at(cls):
        return None
    
    # Relationships
    session = relationship('Session', back_populates='reschedule')
    
    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint(
            "initiator IN ('tutor', 'student')",
            name='check_initiator'
        ),
        CheckConstraint(
            "new_time IS NULL OR new_time > original_time",
            name='check_new_time'
        ),
        Index('ix_reschedules_session_id', 'session_id'),
        Index('ix_reschedules_initiator', 'initiator'),
        Index('ix_reschedules_cancelled_at', 'cancelled_at'),
        Index('ix_reschedules_reason_code', 'reason_code'),
    )
    
    def calculate_hours_before(self) -> Optional[float]:
        """
        Calculate hours between cancelled_at and original_time.
        
        Returns:
            Hours as float, or None if times are not set
        """
        if not self.cancelled_at or not self.original_time:
            return None
        
        delta = self.original_time - self.cancelled_at
        return delta.total_seconds() / 3600.0
    
    def is_last_minute(self) -> bool:
        """
        Check if reschedule was last-minute (<24 hours before).
        
        Returns:
            True if reschedule was <24 hours before original time
        """
        hours = self.calculate_hours_before()
        return hours is not None and hours < 24.0
    
    def __repr__(self) -> str:
        return f"<Reschedule(id={self.id}, session_id={self.session_id}, initiator='{self.initiator}')>"

