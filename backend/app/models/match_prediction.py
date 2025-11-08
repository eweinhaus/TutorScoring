"""
MatchPrediction model representing pre-calculated match predictions.
"""
from typing import TYPE_CHECKING, Optional
from datetime import datetime
from sqlalchemy import Column, String, Integer, Numeric, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, TEXT
from sqlalchemy.orm import relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.student import Student
    from app.models.tutor import Tutor


class MatchPrediction(BaseModel):
    """
    MatchPrediction model storing pre-calculated match predictions.
    
    Relationships:
    - student: Many-to-one relationship with Student model
    - tutor: Many-to-one relationship with Tutor model
    """
    __tablename__ = 'match_predictions'
    
    student_id = Column(UUID(as_uuid=True), ForeignKey('students.id'), nullable=False)
    tutor_id = Column(UUID(as_uuid=True), ForeignKey('tutors.id'), nullable=False)
    
    # Prediction results
    churn_probability = Column(Numeric(5, 4), nullable=False)  # 0.0000 to 1.0000
    risk_level = Column(String(20), nullable=False)  # 'low', 'medium', 'high'
    compatibility_score = Column(Numeric(5, 4), nullable=False)  # 0.0000 to 1.0000
    
    # Feature values (mismatch scores)
    pace_mismatch = Column(Numeric(5, 2), nullable=False)
    style_mismatch = Column(Numeric(5, 2), nullable=False)
    communication_mismatch = Column(Numeric(5, 2), nullable=False)
    age_difference = Column(Integer, nullable=False)
    
    # AI explanation (cached)
    ai_explanation = Column(TEXT, nullable=True)
    
    # Model metadata
    model_version = Column(String(50), nullable=True)  # e.g., 'v1.0', 'v1.1'
    
    # Relationships
    student = relationship('Student', back_populates='match_predictions')
    tutor = relationship('Tutor', back_populates='match_predictions')
    
    # Constraints and Indexes
    __table_args__ = (
        UniqueConstraint('student_id', 'tutor_id', name='uq_match_predictions_student_tutor'),
        Index('ix_match_predictions_student_id', 'student_id'),
        Index('ix_match_predictions_tutor_id', 'tutor_id'),
        Index('ix_match_predictions_risk_level', 'risk_level'),
        Index('ix_match_predictions_churn_probability', 'churn_probability'),
        Index('ix_match_predictions_compatibility_score', 'compatibility_score'),
    )
    
    def __repr__(self) -> str:
        return f"<MatchPrediction(id={self.id}, student_id={self.student_id}, tutor_id={self.tutor_id}, risk_level='{self.risk_level}', churn_probability={self.churn_probability})>"

