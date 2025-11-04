# Sub-PRD: Backend Services & Processing
## Tutor Quality Scoring System - MVP

**Version:** 1.0  
**Parent PRD:** PRD_MVP.md  
**Dependencies:** PRD_Environment_Setup.md, PRD_Data_Foundation.md  
**Status:** Ready for Implementation

---

## 1. Overview

### 1.1 Purpose
Build the FastAPI backend application, API endpoints, Celery background workers, and email service. This phase implements the core business logic and processing pipeline for the tutor scoring system.

### 1.2 Goals
- Create FastAPI REST API for session ingestion and dashboard queries
- Implement Celery background workers for async processing
- Build reschedule rate calculation service
- Integrate email service for automated reports
- Handle 3,000 sessions/day with 1-hour latency

### 1.3 Success Criteria
- ✅ API endpoints functional and tested
- ✅ Background processing handles sessions asynchronously
- ✅ Reschedule rates calculated accurately
- ✅ Email reports sent automatically
- ✅ System processes 3,000 sessions/day within 1-hour latency
- ✅ Error handling and retry logic implemented

---

## 2. FastAPI Application

### 2.1 Application Structure

**File:** `backend/app/main.py`

**Components:**
- FastAPI app instance
- CORS configuration
- Route registration
- Exception handlers
- Middleware (logging, authentication)

**Configuration:**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Tutor Quality Scoring API",
    description="API for tutor performance evaluation",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2.2 API Routes

**Location:** `backend/app/api/`

**Structure:**
```
api/
├── __init__.py
├── routes.py              # Route registration
├── sessions.py            # Session endpoints
├── tutors.py              # Tutor endpoints
└── health.py              # Health check endpoint
```

### 2.3 Session Ingestion Endpoint

**Endpoint:** `POST /api/sessions`

**Purpose:** Receive session data from Rails app (or mock source)

**Request Body:**
```json
{
  "session_id": "uuid",
  "tutor_id": "uuid",
  "student_id": "string",
  "scheduled_time": "2024-01-15T14:00:00Z",
  "completed_time": "2024-01-15T15:30:00Z",
  "status": "completed",
  "duration_minutes": 90,
  "reschedule_info": {
    "initiator": "tutor",
    "reason": "Personal emergency",
    "original_time": "2024-01-15T14:00:00Z",
    "new_time": "2024-01-16T14:00:00Z"
  }
}
```

**Response:**
- `202 Accepted` - Session queued for processing
- `400 Bad Request` - Invalid input data
- `422 Unprocessable Entity` - Validation errors

**Implementation:**
1. Validate request body using Pydantic schema
2. Create session record in database
3. Create reschedule record if applicable
4. Queue Celery task for processing
5. Return accepted response

**Validation:**
- Required fields present
- UUIDs valid format
- Timestamps valid ISO format
- Status enum value
- Reschedule info valid if status is 'rescheduled'

### 2.4 Tutor List Endpoint

**Endpoint:** `GET /api/tutors`

**Purpose:** Retrieve list of tutors with scores for dashboard

**Query Parameters:**
- `risk_status` (optional): Filter by 'high_risk', 'low_risk', 'all'
- `sort_by` (optional): 'reschedule_rate', 'total_sessions', 'name'
- `sort_order` (optional): 'asc', 'desc'
- `limit` (optional): Page size (default 100)
- `offset` (optional): Pagination offset (default 0)

**Response:**
```json
{
  "tutors": [
    {
      "id": "uuid",
      "name": "John Doe",
      "reschedule_rate_30d": 18.5,
      "is_high_risk": true,
      "total_sessions_30d": 27,
      "tutor_reschedules_30d": 5,
      "last_calculated_at": "2024-01-15T10:00:00Z"
    }
  ],
  "total": 100,
  "limit": 100,
  "offset": 0
}
```

**Implementation:**
1. Query tutor_scores with joins to tutors
2. Apply filters
3. Apply sorting
4. Apply pagination
5. Return formatted response

**Performance:**
- Use database indexes for filtering
- Limit result set size
- Optimize queries with joins

### 2.5 Tutor Detail Endpoint

**Endpoint:** `GET /api/tutors/{tutor_id}`

**Purpose:** Retrieve detailed tutor information

**Response:**
```json
{
  "tutor": {
    "id": "uuid",
    "name": "John Doe",
    "email": "john@example.com",
    "created_at": "2023-06-01T00:00:00Z",
    "scores": {
      "reschedule_rate_7d": 20.0,
      "reschedule_rate_30d": 18.5,
      "reschedule_rate_90d": 16.2,
      "is_high_risk": true,
      "last_calculated_at": "2024-01-15T10:00:00Z"
    },
    "statistics": {
      "total_sessions_7d": 10,
      "total_sessions_30d": 27,
      "total_sessions_90d": 85,
      "tutor_reschedules_7d": 2,
      "tutor_reschedules_30d": 5,
      "tutor_reschedules_90d": 14
    }
  }
}
```

**Implementation:**
1. Fetch tutor by ID
2. Fetch tutor_scores record
3. Calculate statistics
4. Return formatted response

### 2.6 Tutor History Endpoint

**Endpoint:** `GET /api/tutors/{tutor_id}/history`

**Purpose:** Retrieve reschedule history for trend analysis

**Query Parameters:**
- `days` (optional): Number of days of history (default 90)
- `limit` (optional): Max results (default 100)

**Response:**
```json
{
  "reschedules": [
    {
      "id": "uuid",
      "session_id": "uuid",
      "original_time": "2024-01-10T14:00:00Z",
      "new_time": "2024-01-11T14:00:00Z",
      "initiator": "tutor",
      "reason": "Personal emergency",
      "hours_before_session": 12.5
    }
  ],
  "trend": {
    "reschedule_rate_by_week": [
      {"week": "2024-01-01", "rate": 15.0},
      {"week": "2024-01-08", "rate": 18.5}
    ]
  }
}
```

**Implementation:**
1. Fetch reschedules for tutor
2. Calculate weekly trends
3. Return formatted response

### 2.7 Health Check Endpoint

**Endpoint:** `GET /api/health`

**Purpose:** System health and status

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "version": "1.0.0"
}
```

---

## 3. Celery Background Workers

### 3.1 Celery Configuration

**File:** `backend/app/tasks/celery_app.py`

**Configuration:**
```python
from celery import Celery
import os

celery_app = Celery(
    "tutor_scoring",
    broker=os.getenv("CELERY_BROKER_URL"),
    backend=os.getenv("CELERY_RESULT_BACKEND")
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max
    task_soft_time_limit=240,  # 4 minutes soft limit
)
```

### 3.2 Session Processing Task

**Task:** `process_session`

**File:** `backend/app/tasks/session_processor.py`

**Purpose:** Process a completed session and update tutor scores

**Steps:**
1. Fetch session record
2. Fetch associated tutor
3. Calculate reschedule rates (if applicable)
4. Update tutor_scores record
5. Generate and send email report
6. Log processing completion

**Error Handling:**
- Retry on database errors (3 attempts)
- Retry on email failures (3 attempts)
- Log all errors
- Mark failed tasks

**Implementation:**
```python
@celery_app.task(bind=True, max_retries=3)
def process_session(self, session_id: str):
    try:
        # Fetch session
        # Calculate scores
        # Update database
        # Send email
        return {"status": "success", "session_id": session_id}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
```

### 3.3 Reschedule Rate Calculator

**Service:** `backend/app/services/reschedule_calculator.py`

**Purpose:** Calculate reschedule rates for a tutor

**Methods:**
- `calculate_reschedule_rate(tutor_id, days)` - Calculate rate for time window
- `update_tutor_scores(tutor_id)` - Update all score windows
- `check_risk_flag(tutor_id, threshold)` - Check and set risk flag

**Algorithm:**
```python
def calculate_reschedule_rate(tutor_id: str, days: int) -> float:
    # Get time window
    start_date = datetime.now() - timedelta(days=days)
    
    # Count total sessions in window
    total_sessions = count_sessions(tutor_id, start_date)
    
    # Count tutor-initiated reschedules
    tutor_reschedules = count_tutor_reschedules(tutor_id, start_date)
    
    # Calculate rate
    if total_sessions == 0:
        return 0.0
    rate = (tutor_reschedules / total_sessions) * 100
    return round(rate, 2)
```

**Time Windows:**
- 7-day rolling window
- 30-day rolling window
- 90-day rolling window

**Risk Flagging:**
- Compare each rate to threshold (default 15%)
- Set `is_high_risk = True` if any rate exceeds threshold
- Update `last_calculated_at` timestamp

### 3.4 Score Update Service

**Service:** `backend/app/services/score_service.py`

**Purpose:** Orchestrate score calculations and updates

**Methods:**
- `update_scores_for_tutor(tutor_id)` - Update all scores for tutor
- `update_scores_for_all_tutors()` - Batch update (for maintenance)
- `recalculate_stale_scores()` - Recalculate scores older than 1 hour

**Implementation:**
1. Calculate 7-day, 30-day, 90-day rates
2. Update tutor_scores record
3. Set risk flags
4. Update timestamps
5. Commit transaction

**Transaction Safety:**
- Use database transactions
- Handle concurrent updates
- Ensure atomicity

---

## 4. Email Service

### 4.1 Email Service Interface

**File:** `backend/app/services/email_service.py`

**Purpose:** Abstract email sending functionality

**Implementation Options:**
- SendGrid (primary)
- AWS SES (alternative)

**Configuration:**
- Service selection via environment variable
- API keys from environment

### 4.2 Email Template

**Template:** HTML email for session reports

**Content:**
- Session details (ID, date, tutor, student)
- Tutor's current reschedule rate
- Risk flag status
- Key insights (e.g., "3 reschedules in past 7 days")
- Link to dashboard
- Mobile-responsive design

**Example:**
```html
<h2>Session Report</h2>
<p><strong>Session:</strong> {session_id}</p>
<p><strong>Tutor:</strong> {tutor_name}</p>
<p><strong>Reschedule Rate (30d):</strong> {rate}%</p>
<p><strong>Status:</strong> {risk_flag}</p>
<p><strong>Insights:</strong> {insights}</p>
<a href="{dashboard_url}">View Dashboard</a>
```

### 4.3 Email Report Generator

**Service:** `backend/app/services/email_report_service.py`

**Methods:**
- `generate_session_report(session_id)` - Create report content
- `send_session_report(session_id, recipient_email)` - Send email
- `format_insights(tutor_id)` - Generate insights text

**Insights Generation:**
- Count recent reschedules
- Identify patterns (e.g., "Frequent reschedules on Fridays")
- Risk level description
- Actionable recommendations

**Example Insights:**
- "Tutor has rescheduled 3 times in the past 7 days"
- "Reschedule rate is 18.5% (above 15% threshold)"
- "Most reschedules occur on weekends"
- "Recommendation: Schedule coaching session"

### 4.4 Email Sending Task

**Task:** `send_email_report`

**File:** `backend/app/tasks/email_tasks.py`

**Purpose:** Send email asynchronously

**Implementation:**
- Queue email task
- Retry on failure (3 attempts)
- Log email status
- Update email_reports table

**Error Handling:**
- Catch email service errors
- Log failures
- Retry with exponential backoff
- Mark as failed if all retries exhausted

---

## 5. Service Layer

### 5.1 Service Organization

**Location:** `backend/app/services/`

**Services:**
- `reschedule_calculator.py` - Reschedule rate calculations
- `score_service.py` - Score update orchestration
- `email_service.py` - Email sending abstraction
- `email_report_service.py` - Report generation
- `tutor_service.py` - Tutor business logic
- `session_service.py` - Session business logic

### 5.2 Business Logic

**Separation of Concerns:**
- API routes: HTTP handling
- Services: Business logic
- Models: Data access
- Tasks: Background processing

### 5.3 Error Handling

**Error Types:**
- Validation errors (400 Bad Request)
- Not found errors (404 Not Found)
- Processing errors (500 Internal Server Error)
- Rate limiting (429 Too Many Requests)

**Error Response Format:**
```json
{
  "error": "Error type",
  "message": "Human-readable message",
  "details": {}
}
```

---

## 6. API Authentication

### 6.1 Authentication Strategy (MVP)

**Simple API Key:**
- API key in request header: `X-API-Key`
- Validate against environment variable
- Reject if invalid

**Future:**
- JWT tokens
- OAuth integration
- User authentication

### 6.2 Middleware

**File:** `backend/app/middleware/auth.py`

**Implementation:**
- Check API key in header
- Validate against configured key
- Reject unauthorized requests

---

## 7. Logging and Monitoring

### 7.1 Logging Configuration

**Setup:**
- Structured logging (JSON format)
- Log levels: DEBUG, INFO, WARNING, ERROR
- Log to stdout (for Render)

**Log Events:**
- API requests/responses
- Task processing
- Email sending
- Errors and exceptions

### 7.2 Monitoring

**Metrics to Track:**
- API request count
- API response times
- Task processing time
- Task queue depth
- Email send success rate
- Error rates

---

## 8. Performance Optimization

### 8.1 Database Optimization

**Query Optimization:**
- Use indexes for filtering
- Limit result sets
- Use select_related for joins
- Cache frequently accessed data

### 8.2 Task Processing Optimization

**Batch Processing:**
- Process multiple sessions in batch
- Reduce database round trips
- Optimize score calculations

### 8.3 Caching Strategy

**Redis Caching:**
- Cache tutor scores (5-minute TTL)
- Cache tutor list queries
- Invalidate on updates

---

## 9. Testing

### 9.1 Unit Tests

**Location:** `backend/tests/`

**Test Areas:**
- API endpoints
- Service methods
- Calculation logic
- Email templates

### 9.2 Integration Tests

**Test Areas:**
- End-to-end API flows
- Task processing
- Database operations
- Email sending (mock)

### 9.3 Performance Tests

**Test Areas:**
- API response times
- Concurrent request handling
- Task processing throughput
- Database query performance

---

## 10. Deployment Configuration

### 10.1 Render Configuration

**Web Service:**
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Environment variables: Set all required vars
- Health check: `/api/health`

**Background Worker:**
- Start command: `celery -A app.tasks.celery_app worker --loglevel=info`
- Same environment variables as web service

### 10.2 Environment Variables

**Required:**
- DATABASE_URL
- REDIS_URL
- CELERY_BROKER_URL
- EMAIL_SERVICE
- SENDGRID_API_KEY (or AWS credentials)
- ADMIN_EMAIL
- SECRET_KEY
- API_KEY

---

## 11. Success Criteria

### 11.1 Functional Requirements

- [ ] All API endpoints implemented and tested
- [ ] Session ingestion works correctly
- [ ] Tutor queries return accurate data
- [ ] Background processing handles sessions
- [ ] Reschedule rates calculated correctly
- [ ] Email reports sent automatically
- [ ] Error handling works correctly

### 11.2 Performance Requirements

- [ ] API response time <500ms (p95)
- [ ] Processes 3,000 sessions/day
- [ ] 1-hour processing latency maintained
- [ ] Handles concurrent requests
- [ ] Task queue processes efficiently

### 11.3 Reliability Requirements

- [ ] Retry logic works for failed tasks
- [ ] No data loss on failures
- [ ] Email failures handled gracefully
- [ ] Database transactions atomic
- [ ] Error logging comprehensive

---

## 12. Dependencies

### 12.1 Required

- Data Foundation complete (PRD_Data_Foundation.md)
- Database schema deployed
- Models available
- Synthetic data for testing

### 12.2 External Services

- SendGrid account (or AWS SES)
- Email configured
- API keys available

---

## 13. Next Steps

After completing Backend Services:

1. **Frontend Dashboard** (Next Sub-PRD)
   - React application
   - API integration
   - Dashboard UI components
   - Visualizations

