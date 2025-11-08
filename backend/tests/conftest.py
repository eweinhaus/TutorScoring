"""
Pytest configuration and fixtures.
"""
import pytest
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.dialects.sqlite import BLOB
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.models import Base, Tutor, Session, Reschedule, TutorScore, EmailReport, Student, MatchPrediction
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.types import TypeDecorator, CHAR
from decimal import Decimal
import uuid


# Use PostgreSQL test database (same as production)
# Fall back to SQLite if DATABASE_URL not set (for CI/CD)
TEST_DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///:memory:')


class GUID(TypeDecorator):
    """Platform-independent GUID type for SQLite compatibility."""
    impl = CHAR
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID())
        else:
            return dialect.type_descriptor(CHAR(36))
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return str(uuid.UUID(value))
            return str(value)
    
    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            return value


@pytest.fixture(scope="function")
def db_session():
    """
    Create a fresh database session for each test.
    Uses PostgreSQL if available, otherwise SQLite.
    """
    # Map UUID to GUID for SQLite compatibility
    if 'sqlite' in TEST_DATABASE_URL:
        # Replace UUID columns with GUID for SQLite
        for table in Base.metadata.tables.values():
            for col in table.columns:
                if isinstance(col.type, PG_UUID):
                    col.type = GUID()
    
    if 'sqlite' in TEST_DATABASE_URL:
        engine = create_engine(
            TEST_DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    else:
        engine = create_engine(TEST_DATABASE_URL)
    
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Only drop tables if using test database
        if 'sqlite' in TEST_DATABASE_URL or 'test' in TEST_DATABASE_URL.lower():
            Base.metadata.drop_all(engine)


@pytest.fixture
def sample_tutor(db_session):
    """Create a sample tutor for testing."""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    tutor = Tutor(
        name=f"John Doe {unique_id}",
        email=f"john.doe.{unique_id}@example.com",
        is_active=True
    )
    db_session.add(tutor)
    db_session.commit()
    db_session.refresh(tutor)
    return tutor


@pytest.fixture
def sample_session(db_session, sample_tutor):
    """Create a sample session for testing."""
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    session = Session(
        tutor_id=sample_tutor.id,
        student_id=f"student_{unique_id}",
        scheduled_time=datetime.utcnow(),
        completed_time=datetime.utcnow() + timedelta(minutes=60),
        status="completed",
        duration_minutes=60
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session


@pytest.fixture
def sample_reschedule(db_session, sample_session):
    """Create a sample reschedule for testing."""
    reschedule = Reschedule(
        session_id=sample_session.id,
        initiator="tutor",
        original_time=sample_session.scheduled_time,
        new_time=sample_session.scheduled_time + timedelta(days=1),
        reason="Personal emergency",
        reason_code="personal",
        cancelled_at=sample_session.scheduled_time - timedelta(hours=12),
        hours_before_session=Decimal("12.00")
    )
    db_session.add(reschedule)
    db_session.commit()
    db_session.refresh(reschedule)
    return reschedule


@pytest.fixture
def sample_tutor_score(db_session, sample_tutor):
    """Create a sample tutor score for testing."""
    tutor_score = TutorScore(
        tutor_id=sample_tutor.id,
        reschedule_rate_7d=Decimal("5.00"),
        reschedule_rate_30d=Decimal("8.50"),
        reschedule_rate_90d=Decimal("10.00"),
        total_sessions_7d=20,
        total_sessions_30d=80,
        total_sessions_90d=200,
        tutor_reschedules_7d=1,
        tutor_reschedules_30d=7,
        tutor_reschedules_90d=20,
        is_high_risk=False,
        risk_threshold=Decimal("15.00"),
        last_calculated_at=datetime.utcnow()
    )
    db_session.add(tutor_score)
    db_session.commit()
    db_session.refresh(tutor_score)
    return tutor_score


@pytest.fixture
def sample_email_report(db_session, sample_session):
    """Create a sample email report for testing."""
    email_report = EmailReport(
        session_id=sample_session.id,
        recipient_email="admin@example.com",
        sent_at=datetime.utcnow(),
        status="sent",
        error_message=None
    )
    db_session.add(email_report)
    db_session.commit()
    db_session.refresh(email_report)
    return email_report

