"""
Student model representing student profiles with preferences.
"""
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Column, String, Integer, Index
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.match_prediction import MatchPrediction


class Student(BaseModel):
    """
    Student model representing a student profile with matching preferences.
    
    Relationships:
    - match_predictions: One-to-many relationship with MatchPrediction model
    """
    __tablename__ = 'students'
    
    name = Column(String(255), nullable=False)
    age = Column(Integer, nullable=False)
    sex = Column(String(10), nullable=True)  # 'male', 'female', 'other', or None
    preferred_pace = Column(Integer, nullable=False)  # 1-5 scale (1=slow, 5=fast)
    preferred_teaching_style = Column(String(50), nullable=False)  # e.g., 'structured', 'flexible', 'interactive'
    communication_style_preference = Column(Integer, nullable=False)  # 1-5 scale (1=formal, 5=casual)
    urgency_level = Column(Integer, nullable=False)  # 1-5 scale (1=low urgency, 5=high urgency)
    learning_goals = Column(String(500), nullable=True)  # Free text
    previous_tutoring_experience = Column(Integer, nullable=False, default=0)  # Number of sessions
    previous_satisfaction = Column(Integer, nullable=True)  # 1-5 scale (1=very dissatisfied, 5=very satisfied)
    preferences_json = Column(JSON, nullable=True)  # Additional flexible preferences
    
    # Relationships
    match_predictions = relationship(
        'MatchPrediction',
        back_populates='student',
        cascade='all, delete-orphan'
    )
    
    # Indexes
    __table_args__ = (
        Index('ix_students_age', 'age'),
        Index('ix_students_preferred_pace', 'preferred_pace'),
        Index('ix_students_created_at', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<Student(id={self.id}, name='{self.name}', age={self.age}, preferred_pace={self.preferred_pace})>"

