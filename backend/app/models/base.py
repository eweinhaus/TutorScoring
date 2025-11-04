"""
Base model with common fields for all database models.
"""
from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
import uuid

Base = declarative_base()


class BaseModel(Base):
    """
    Abstract base model with common fields.
    
    All models inherit from this class to get:
    - id: UUID primary key
    - created_at: Timestamp when record was created
    - updated_at: Timestamp when record was last updated
    """
    __abstract__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

