"""
EmailReport model representing sent email reports.
"""
from typing import TYPE_CHECKING, Optional
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declared_attr

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.session import Session


class EmailReport(BaseModel):
    """
    EmailReport model tracking sent email reports for sessions.
    
    Note: This model does not have updated_at field per PRD specification.
    We'll manually exclude it in the migration.
    
    Relationships:
    - session: Many-to-one relationship with Session model
    
    Constraints:
    - status must be 'sent', 'failed', or 'pending'
    """
    __tablename__ = 'email_reports'
    
    session_id = Column(UUID(as_uuid=True), ForeignKey('sessions.id'), nullable=False)
    recipient_email = Column(String(255), nullable=False)
    sent_at = Column(DateTime, nullable=False)
    status = Column(String(50), nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Note: No updated_at field per PRD specification
    # Override to exclude updated_at from this model
    @declared_attr
    def updated_at(cls):
        return None
    
    # Relationships
    session = relationship('Session', back_populates='email_report')
    
    # Constraints and Indexes
    __table_args__ = (
        CheckConstraint(
            "status IN ('sent', 'failed', 'pending')",
            name='check_email_status'
        ),
        Index('ix_email_reports_session_id', 'session_id'),
        Index('ix_email_reports_sent_at', 'sent_at'),
        Index('ix_email_reports_status', 'status'),
    )
    
    def mark_sent(self) -> None:
        """Mark email report as sent."""
        from datetime import datetime
        self.status = 'sent'
        self.sent_at = datetime.utcnow()
        self.error_message = None
    
    def mark_failed(self, error_message: str) -> None:
        """
        Mark email report as failed with error message.
        
        Args:
            error_message: Error message describing the failure
        """
        from datetime import datetime
        self.status = 'failed'
        self.sent_at = datetime.utcnow()
        self.error_message = error_message
    
    def __repr__(self) -> str:
        return f"<EmailReport(id={self.id}, session_id={self.session_id}, status='{self.status}')>"

