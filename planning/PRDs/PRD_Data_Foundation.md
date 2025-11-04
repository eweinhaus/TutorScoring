# Sub-PRD: Data Foundation & Models
## Tutor Quality Scoring System - MVP

**Version:** 1.0  
**Parent PRD:** PRD_MVP.md  
**Dependencies:** PRD_Environment_Setup.md  
**Status:** Ready for Implementation

---

## 1. Overview

### 1.1 Purpose
Design and implement the database schema, SQLAlchemy models, and synthetic data generation system. This phase establishes the data layer foundation that all other components depend on.

### 1.2 Goals
- Design comprehensive database schema for tutor scoring system
- Implement SQLAlchemy ORM models with proper relationships
- Create database migrations using Alembic
- Build synthetic data generator for realistic test data
- Establish data validation and constraints

### 1.3 Success Criteria
- ✅ Database schema supports all MVP requirements
- ✅ Models correctly represent relationships and constraints
- ✅ Migrations can be applied cleanly
- ✅ Synthetic data generator creates realistic datasets
- ✅ Data quality meets requirements (realistic distributions, patterns)

---

## 2. Database Schema Design

### 2.1 Entity Relationship Overview

```
tutors (1) ──< (many) sessions
sessions (1) ──< (0 or 1) reschedules
tutors (1) ──< (1) tutor_scores
sessions (1) ──< (0 or 1) email_reports
```

### 2.2 Core Tables

#### 2.2.1 `tutors` Table
**Purpose:** Store tutor profile information and metadata

**Columns:**
- `id` (UUID, Primary Key) - Unique tutor identifier
- `name` (VARCHAR(255), NOT NULL) - Tutor full name
- `email` (VARCHAR(255), UNIQUE) - Tutor email (optional)
- `created_at` (TIMESTAMP, NOT NULL) - Account creation timestamp
- `updated_at` (TIMESTAMP, NOT NULL) - Last update timestamp
- `is_active` (BOOLEAN, DEFAULT true) - Active status flag

**Indexes:**
- Primary key on `id`
- Index on `email` (for lookups)
- Index on `created_at` (for time-based queries)

#### 2.2.2 `sessions` Table
**Purpose:** Store all session records (completed, rescheduled, no-show)

**Columns:**
- `id` (UUID, Primary Key) - Unique session identifier
- `tutor_id` (UUID, Foreign Key → tutors.id, NOT NULL) - Associated tutor
- `student_id` (VARCHAR(255), NOT NULL) - Student identifier
- `scheduled_time` (TIMESTAMP, NOT NULL) - Originally scheduled time
- `completed_time` (TIMESTAMP, NULLABLE) - Actual completion time
- `status` (VARCHAR(50), NOT NULL) - Status enum: 'completed', 'rescheduled', 'no_show'
- `duration_minutes` (INTEGER, NULLABLE) - Session duration if completed
- `created_at` (TIMESTAMP, NOT NULL) - Record creation time
- `updated_at` (TIMESTAMP, NOT NULL) - Last update time

**Constraints:**
- `status` must be one of: 'completed', 'rescheduled', 'no_show'
- `completed_time` must be NULL if status is 'rescheduled' or 'no_show'
- `completed_time` must be >= `scheduled_time` if not NULL

**Indexes:**
- Primary key on `id`
- Foreign key index on `tutor_id`
- Index on `scheduled_time` (for time-range queries)
- Index on `status` (for filtering)
- Composite index on `(tutor_id, scheduled_time)` (for tutor history queries)

#### 2.2.3 `reschedules` Table
**Purpose:** Track reschedule events with detailed metadata

**Columns:**
- `id` (UUID, Primary Key) - Unique reschedule identifier
- `session_id` (UUID, Foreign Key → sessions.id, UNIQUE, NOT NULL) - Associated session
- `initiator` (VARCHAR(50), NOT NULL) - Who initiated: 'tutor' or 'student'
- `original_time` (TIMESTAMP, NOT NULL) - Original scheduled time
- `new_time` (TIMESTAMP, NULLABLE) - New scheduled time (NULL if cancelled)
- `reason` (TEXT, NULLABLE) - Reschedule reason text
- `reason_code` (VARCHAR(100), NULLABLE) - Categorized reason (e.g., 'personal', 'emergency')
- `cancelled_at` (TIMESTAMP, NOT NULL) - When reschedule was initiated
- `hours_before_session` (DECIMAL(10,2), NULLABLE) - Hours before original session
- `created_at` (TIMESTAMP, NOT NULL) - Record creation time

**Constraints:**
- `initiator` must be 'tutor' or 'student'
- `original_time` must match associated session's `scheduled_time`
- `new_time` must be > `original_time` if not NULL
- `hours_before_session` = (original_time - cancelled_at) / 3600

**Indexes:**
- Primary key on `id`
- Foreign key index on `session_id`
- Index on `initiator` (for filtering tutor-initiated reschedules)
- Index on `cancelled_at` (for time-based analysis)
- Index on `reason_code` (for pattern analysis)

#### 2.2.4 `tutor_scores` Table
**Purpose:** Store calculated risk scores and flags for tutors

**Columns:**
- `id` (UUID, Primary Key) - Unique score record identifier
- `tutor_id` (UUID, Foreign Key → tutors.id, UNIQUE, NOT NULL) - Associated tutor
- `reschedule_rate_7d` (DECIMAL(5,2), NULLABLE) - 7-day reschedule rate percentage
- `reschedule_rate_30d` (DECIMAL(5,2), NULLABLE) - 30-day reschedule rate percentage
- `reschedule_rate_90d` (DECIMAL(5,2), NULLABLE) - 90-day reschedule rate percentage
- `total_sessions_7d` (INTEGER, DEFAULT 0) - Total sessions in 7 days
- `total_sessions_30d` (INTEGER, DEFAULT 0) - Total sessions in 30 days
- `total_sessions_90d` (INTEGER, DEFAULT 0) - Total sessions in 90 days
- `tutor_reschedules_7d` (INTEGER, DEFAULT 0) - Tutor-initiated reschedules in 7 days
- `tutor_reschedules_30d` (INTEGER, DEFAULT 0) - Tutor-initiated reschedules in 30 days
- `tutor_reschedules_90d` (INTEGER, DEFAULT 0) - Tutor-initiated reschedules in 90 days
- `is_high_risk` (BOOLEAN, DEFAULT false) - Risk flag (exceeds threshold)
- `risk_threshold` (DECIMAL(5,2), DEFAULT 15.00) - Threshold used for flagging
- `last_calculated_at` (TIMESTAMP, NOT NULL) - Last score calculation time
- `created_at` (TIMESTAMP, NOT NULL) - Record creation time
- `updated_at` (TIMESTAMP, NOT NULL) - Last update time

**Constraints:**
- Reschedule rates must be between 0 and 100
- `is_high_risk` = true if any reschedule rate > `risk_threshold`
- `tutor_id` must be unique (one score record per tutor)

**Indexes:**
- Primary key on `id`
- Foreign key index on `tutor_id`
- Index on `is_high_risk` (for filtering at-risk tutors)
- Index on `last_calculated_at` (for identifying stale scores)

#### 2.2.5 `email_reports` Table
**Purpose:** Track sent email reports for audit and debugging

**Columns:**
- `id` (UUID, Primary Key) - Unique report identifier
- `session_id` (UUID, Foreign Key → sessions.id, NOT NULL) - Associated session
- `recipient_email` (VARCHAR(255), NOT NULL) - Email recipient
- `sent_at` (TIMESTAMP, NOT NULL) - When email was sent
- `status` (VARCHAR(50), NOT NULL) - Status: 'sent', 'failed', 'pending'
- `error_message` (TEXT, NULLABLE) - Error details if failed
- `created_at` (TIMESTAMP, NOT NULL) - Record creation time

**Indexes:**
- Primary key on `id`
- Foreign key index on `session_id`
- Index on `sent_at` (for time-based queries)
- Index on `status` (for filtering failed reports)

---

## 3. SQLAlchemy Models

### 3.1 Model Structure

**Location:** `backend/app/models/`

**Files:**
- `__init__.py` - Model exports
- `tutor.py` - Tutor model
- `session.py` - Session model
- `reschedule.py` - Reschedule model
- `tutor_score.py` - TutorScore model
- `email_report.py` - EmailReport model
- `base.py` - Base model with common fields

### 3.2 Base Model

**File:** `backend/app/models/base.py`

```python
from sqlalchemy import Column, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
```

### 3.3 Tutor Model

**File:** `backend/app/models/tutor.py`

**Key Features:**
- Relationship to sessions (one-to-many)
- Relationship to tutor_scores (one-to-one)
- Methods: `get_reschedule_rate()`, `calculate_risk_score()`

**Relationships:**
- `sessions` - List of associated sessions
- `tutor_score` - Associated score record

### 3.4 Session Model

**File:** `backend/app/models/session.py`

**Key Features:**
- Relationship to tutor (many-to-one)
- Relationship to reschedule (one-to-one, optional)
- Relationship to email_report (one-to-one, optional)
- Methods: `is_rescheduled()`, `is_completed()`, `get_duration()`

**Relationships:**
- `tutor` - Associated tutor
- `reschedule` - Reschedule event (if applicable)
- `email_report` - Email report (if sent)

### 3.5 Reschedule Model

**File:** `backend/app/models/reschedule.py`

**Key Features:**
- Relationship to session (one-to-one)
- Methods: `calculate_hours_before()`, `is_last_minute()`

**Relationships:**
- `session` - Associated session

### 3.6 TutorScore Model

**File:** `backend/app/models/tutor_score.py`

**Key Features:**
- Relationship to tutor (one-to-one)
- Methods: `update_rates()`, `check_risk_flag()`, `to_dict()`

**Relationships:**
- `tutor` - Associated tutor

### 3.7 EmailReport Model

**File:** `backend/app/models/email_report.py`

**Key Features:**
- Relationship to session (many-to-one)
- Methods: `mark_sent()`, `mark_failed()`

**Relationships:**
- `session` - Associated session

### 3.8 Model Validation

**Pydantic Schemas:**
- Create Pydantic schemas for API validation
- Location: `backend/app/schemas/`
- Separate schemas for request/response models

---

## 4. Database Migrations

### 4.1 Alembic Configuration

**File:** `backend/alembic.ini`
- Configure database URL from environment
- Set migration directory

**File:** `backend/alembic/env.py`
- Import models for autogenerate
- Configure SQLAlchemy engine
- Set target metadata

### 4.2 Initial Migration

**Migration:** `001_initial_schema.py`

**Steps:**
1. Create all tables in correct order (respecting foreign keys)
2. Add indexes
3. Add constraints
4. Set default values

**Order:**
1. `tutors`
2. `sessions` (depends on tutors)
3. `reschedules` (depends on sessions)
4. `tutor_scores` (depends on tutors)
5. `email_reports` (depends on sessions)

### 4.3 Migration Best Practices

- Always create migrations for schema changes
- Test migrations on sample data
- Include rollback (downgrade) functions
- Document migration purpose in commit message

---

## 5. Synthetic Data Generator

### 5.1 Generator Script

**File:** `scripts/generate_data.py`

**Purpose:** Generate realistic test data for development and demo

### 5.2 Data Requirements

#### 5.2.1 Tutor Data
- **Quantity:** 75-100 tutors
- **Distribution:**
  - 60% low-risk (0-10% reschedule rate)
  - 25% medium-risk (10-20% reschedule rate)
  - 15% high-risk (>20% reschedule rate)
- **Attributes:**
  - Realistic names (use Faker library)
  - Varied creation dates (past 6 months)
  - Mix of active/inactive tutors (90% active)

#### 5.2.2 Session Data
- **Quantity:** 3,000+ sessions over past 90 days
- **Distribution:**
  - 70% completed
  - 25% rescheduled (of which 98.2% tutor-initiated)
  - 5% no-show
- **Temporal Patterns:**
  - More sessions on weekdays
  - Peak hours: 3-8 PM
  - Seasonal variation (more in fall/winter)
- **Attributes:**
  - Realistic scheduled times
  - Varied durations (30-120 minutes)
  - Student IDs (varied, some repeat customers)

#### 5.2.3 Reschedule Data
- **Patterns:**
  - High-risk tutors: Frequent reschedules (weekly)
  - Medium-risk tutors: Occasional reschedules (monthly)
  - Low-risk tutors: Rare reschedules (quarterly)
- **Timing:**
  - 40% last-minute (<24 hours before)
  - 60% planned (>24 hours before)
- **Reasons:**
  - Common: "Personal emergency", "Scheduling conflict", "Family issue"
  - Less common: "Technical issues", "Health concern"
  - Distribution: Some tutors have repeated reasons

#### 5.2.4 Tutor Scores Data
- **Calculation:**
  - Generate based on actual reschedule history
  - Calculate 7-day, 30-day, 90-day rates
  - Set risk flags based on threshold (15%)
- **Realistic Values:**
  - Most tutors: 0-15% reschedule rate
  - High-risk tutors: 20-40% reschedule rate
  - Some tutors with very high rates (40-60%)

### 5.3 Generator Implementation

**Features:**
- Use `faker` library for realistic names, emails
- Use `random` with weighted distributions
- Generate time-based patterns (weekdays, peak hours)
- Create correlations (high-risk tutors have patterns)
- Ensure referential integrity
- Option to clear existing data before generating
- Configurable quantities via command-line arguments

**Command-Line Interface:**
```bash
python scripts/generate_data.py \
  --tutors 100 \
  --sessions 3000 \
  --days 90 \
  --clear-existing
```

**Output:**
- Progress indicators
- Summary statistics
- Validation report
- Data quality metrics

### 5.4 Data Quality Checks

**Validation:**
- All foreign keys valid
- Reschedule rates match actual data
- Tutor scores calculated correctly
- Temporal patterns realistic
- No orphaned records

**Statistics Report:**
- Total tutors, sessions, reschedules
- Reschedule rate distribution
- High-risk tutor count
- Data coverage (date ranges)

---

## 6. Database Initialization

### 6.1 Setup Script

**File:** `scripts/setup_db.py`

**Purpose:** Initialize database with schema and seed data

**Steps:**
1. Create database if not exists
2. Run Alembic migrations
3. Optionally generate synthetic data
4. Verify setup

**Usage:**
```bash
python scripts/setup_db.py --init --seed-data
```

### 6.2 Seed Data

**Optional:** Create minimal seed data for development
- 5-10 sample tutors
- 50-100 sample sessions
- Mix of risk levels

---

## 7. Data Validation

### 7.1 Model-Level Validation

**SQLAlchemy Constraints:**
- Check constraints for enum values
- Foreign key constraints
- Unique constraints
- Not null constraints

### 7.2 Application-Level Validation

**Pydantic Schemas:**
- Input validation for API requests
- Output validation for API responses
- Type checking and conversion

### 7.3 Business Logic Validation

**Examples:**
- Reschedule rate must be 0-100%
- Completed sessions must have completion time
- Reschedule new_time must be after original_time
- Tutor scores must match calculated values

---

## 8. Testing

### 8.1 Unit Tests

**Location:** `backend/tests/models/`

**Test Cases:**
- Model creation and relationships
- Model methods and calculations
- Constraint validation
- Enum value validation

### 8.2 Integration Tests

**Test Cases:**
- Database migrations
- Data generation and validation
- Foreign key relationships
- Query performance

### 8.3 Data Quality Tests

**Test Cases:**
- Synthetic data distributions
- Reschedule rate calculations
- Risk flag accuracy
- Data completeness

---

## 9. Performance Considerations

### 9.1 Indexing Strategy

**Critical Indexes:**
- Foreign keys (automatic)
- Time-based queries (scheduled_time, created_at)
- Filter columns (status, is_high_risk, initiator)
- Composite indexes for common query patterns

### 9.2 Query Optimization

**Best Practices:**
- Use eager loading for relationships
- Avoid N+1 queries
- Use database aggregation for calculations
- Cache frequently accessed data

### 9.3 Scalability

**Future Considerations:**
- Partitioning for large tables (sessions)
- Read replicas for dashboard queries
- Archiving old data

---

## 10. Success Criteria

### 10.1 Technical Validation

- [ ] All tables created successfully
- [ ] All relationships working correctly
- [ ] Migrations can be applied and rolled back
- [ ] Synthetic data generator produces realistic data
- [ ] Data quality checks pass
- [ ] Models validate correctly

### 10.2 Data Quality

- [ ] Reschedule rates calculated accurately
- [ ] Risk flags set correctly
- [ ] Temporal patterns realistic
- [ ] Data distributions match requirements
- [ ] No orphaned or invalid records

### 10.3 Ready for Integration

- [ ] Models can be imported by services
- [ ] Database ready for API endpoints
- [ ] Test data available for development
- [ ] Documentation complete

---

## 11. Dependencies

### 11.1 Required

- Environment setup complete (PRD_Environment_Setup.md)
- PostgreSQL database accessible
- Python dependencies installed
- Alembic configured

### 11.2 Optional

- Faker library for realistic data generation
- Data validation tools
- Testing frameworks

---

## 12. Next Steps

After completing Data Foundation:

1. **Backend Services & Processing** (Next Sub-PRD)
   - FastAPI application using these models
   - API endpoints for data access
   - Celery tasks for score calculation

2. **Frontend Dashboard** (Following Sub-PRD)
   - React app consuming API data
   - Visualizations using this data structure

