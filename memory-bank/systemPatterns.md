# System Patterns
## Tutor Quality Scoring System

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────┐
│   React     │  Frontend Dashboard
│  Dashboard  │
└──────┬──────┘
       │ HTTP/REST
┌──────▼──────┐
│   FastAPI   │  REST API
│   Backend   │
└──────┬──────┘
       │
   ┌───┴───┐
   │       │
┌──▼──┐ ┌──▼──┐
│PostgreSQL│ │Redis│
│ Database │ │Queue│
└─────┘ └──┬──┘
           │
      ┌────▼────┐
      │ Celery  │  Background Workers
      │ Workers │
      └─────────┘
```

### Component Layers

1. **Frontend Layer:** React dashboard (static hosting)
2. **API Layer:** FastAPI REST API (Render web service)
3. **Processing Layer:** Celery workers (Render background workers)
4. **Data Layer:** PostgreSQL + Redis (Render managed services)

---

## Data Flow Patterns

### Session Processing Flow

```
1. Session Complete (Rails/Mock)
   ↓
2. POST /api/sessions → FastAPI
   ↓
3. Create Session Record → PostgreSQL
   ↓
4. Queue Celery Task → Redis
   ↓
5. Worker Processes Session
   ↓
6. Calculate Reschedule Rates
   ↓
7. Update Tutor Scores → PostgreSQL
   ↓
8. Generate Email Report
   ↓
9. Send Email → SendGrid/SES
   ↓
10. Dashboard Updates (Polling)
```

### Dashboard Query Flow

```
1. User Opens Dashboard
   ↓
2. React Query → GET /api/tutors
   ↓
3. FastAPI Queries PostgreSQL
   ↓
4. Returns Tutor List + Scores
   ↓
5. Dashboard Renders Components
   ↓
6. Polls Every 30 Seconds
```

---

## Database Schema Patterns

### Core Tables

1. **tutors** - Tutor profiles (one-to-many with sessions)
2. **sessions** - Session records (many-to-one with tutors)
3. **reschedules** - Reschedule events (one-to-one with sessions)
4. **tutor_scores** - Calculated scores (one-to-one with tutors)
5. **email_reports** - Email history (many-to-one with sessions)

### Relationship Pattern

```
tutors (1) ──< (many) sessions
sessions (1) ──< (0 or 1) reschedules
tutors (1) ──< (1) tutor_scores
sessions (1) ──< (0 or 1) email_reports
```

### Key Design Patterns

- **UUID Primary Keys:** All tables use UUID for IDs
- **Timestamps:** Created/updated timestamps on all tables
- **Soft Deletes:** `is_active` flag on tutors (future: soft delete)
- **Audit Trail:** `email_reports` table tracks all sent emails
- **Denormalized Scores:** `tutor_scores` table stores calculated values for performance

---

## API Design Patterns

### RESTful Endpoints (Implemented)

- **POST /api/sessions** - Session ingestion (async, returns 202) ✅
  - Requires X-API-Key header
  - Validates session data
  - Creates session and reschedule if needed
  - Queues Celery task for processing
  
- **GET /api/tutors** - List tutors with filters/sorting ✅
  - Query params: risk_status, sort_by, sort_order, limit, offset
  - Returns paginated list with scores
  
- **GET /api/tutors/{id}** - Tutor detail ✅
  - Returns tutor with scores and statistics
  - Includes reschedule rates (7d, 30d, 90d)
  
- **GET /api/tutors/{id}/history** - Reschedule history ✅
  - Returns reschedule events and weekly trends
  - Query params: days, limit
  
- **GET /api/health** - Health check ✅
  - Returns database and Redis connection status

### Request/Response Patterns

**Session Ingestion:**
- Async pattern: Accept request, queue job, return immediately
- Validation: Pydantic schemas for input validation
- Error handling: 400 for validation, 500 for server errors

**Query Endpoints:**
- Filtering: Query parameters for filters
- Pagination: limit/offset pattern
- Sorting: sort_by/sort_order parameters
- Response: Consistent JSON structure with data/metadata

### Authentication Pattern

**MVP:** Simple API key in header (`X-API-Key`)
**Future:** JWT tokens, OAuth integration

---

## Background Processing Patterns

### Celery Task Pattern

**Task Definition:**
```python
@celery_app.task(bind=True, max_retries=3)
def process_session(self, session_id: str):
    try:
        # Process session
        # Update scores
        # Send email
        return {"status": "success"}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
```

**Error Handling:**
- Retry with exponential backoff
- Max 3 retries
- Log all failures
- Mark permanently failed if all retries exhausted

### Queue Pattern

- **Broker:** Redis (message broker)
- **Result Backend:** Redis (task results)
- **Task Tracking:** Track started tasks
- **Time Limits:** Soft limit 4 min, hard limit 5 min

---

## Service Layer Patterns

### Separation of Concerns (Implemented)

- **API Routes:** HTTP handling, validation ✅
  - Located in `app/api/` directory
  - Use Pydantic schemas for validation
  - Return appropriate HTTP status codes
  
- **Services:** Business logic, calculations ✅
  - `reschedule_calculator.py` - Rate calculations
  - `score_service.py` - Score updates and risk flagging
  - `tutor_service.py` - Tutor queries with filtering
  - `session_service.py` - Session creation
  - `email_service.py` - Email sending abstraction
  - `email_report_service.py` - Report generation
  
- **Models:** Data access, relationships ✅
  - SQLAlchemy ORM models
  - Relationships properly configured
  - Constraints and indexes in place
  
- **Tasks:** Background processing ✅
  - `session_processor.py` - Processes sessions, updates scores
  - `email_tasks.py` - Sends email reports
  - Retry logic with exponential backoff

### Service Pattern Example

```python
# Service layer handles business logic
class RescheduleCalculator:
    def calculate_rate(tutor_id, days):
        # Business logic here
        
# API route delegates to service
@router.post("/sessions")
def create_session(session_data):
    # Validate input
    # Create record
    # Queue task
    return {"status": "queued"}
```

---

## Frontend Patterns

### Component Structure

```
pages/
  ├── Dashboard.jsx      # Main overview
  ├── TutorList.jsx     # List view
  └── TutorDetail.jsx   # Detail view

components/
  ├── common/           # Reusable components
  ├── tutor/           # Tutor-specific
  └── charts/          # Chart components
```

### Data Fetching Pattern

**React Query Pattern:**
- Server state managed by React Query
- Automatic caching and refetching
- Polling for real-time updates (30-second interval)
- Loading and error states handled

**Custom Hooks:**
- `useTutors()` - Fetch tutor list
- `useTutorDetail(id)` - Fetch tutor detail
- Encapsulate API calls and caching

### State Management Pattern

- **Server State:** React Query (API data)
- **Local State:** React useState (UI state, filters)
- **Context:** Not needed for MVP (simple state)

---

## Error Handling Patterns

### Backend Error Handling

**API Errors:**
- Validation errors: 400 Bad Request
- Not found: 404 Not Found
- Server errors: 500 Internal Server Error
- Consistent error response format

**Task Errors:**
- Retry logic with exponential backoff
- Log all errors
- Track failed tasks
- Alert on persistent failures

### Frontend Error Handling

**React Query Errors:**
- Error boundaries for component errors
- Error messages displayed to user
- Retry functionality
- Fallback UI for errors

---

## Performance Patterns

### Database Optimization (Implemented)

- **Indexes:** Foreign keys, time-based queries, filter columns ✅
  - All foreign keys indexed
  - Time-based columns indexed (scheduled_time, created_at)
  - Filter columns indexed (status, is_high_risk)
  
- **Query Optimization:** Eager loading, avoid N+1 queries ✅
  - Uses `joinedload` for eager loading tutor scores
  - Optimized tutor list queries with proper joins
  
- **Caching:** Redis cache for frequently accessed data ✅
  - Tutor scores cached with 5-minute TTL
  - Cache invalidation on score updates
  - Graceful fallback if Redis unavailable

### API Optimization

- **Response Time:** <500ms for dashboard queries
- **Pagination:** Limit result sets
- **Caching:** Cache tutor scores (5-minute TTL)

### Frontend Optimization

- **Code Splitting:** Lazy load routes
- **Memoization:** React.memo for expensive components
- **Loading States:** Show loading indicators during fetches

---

## Security Patterns

### MVP Security

- **API Authentication:** API key in header
- **Input Validation:** Pydantic schemas validate all inputs
- **SQL Injection:** SQLAlchemy ORM prevents injection
- **CORS:** Configured for frontend origin only

### Future Security

- **JWT Tokens:** User authentication
- **Encryption:** Encrypt sensitive data at rest
- **Rate Limiting:** Prevent abuse
- **Audit Logging:** Track all actions

---

## Deployment Patterns

### Render Deployment

**Services:**
- Web Service: FastAPI application
- Background Worker: Celery worker
- PostgreSQL: Managed database
- Redis: Managed Redis instance
- Static Site: Frontend dashboard

**Configuration:**
- Environment variables from Render dashboard
- Build commands in render.yaml
- Health checks for monitoring

### Migration Pattern (Render → AWS)

- Same architecture, swap infrastructure
- Render Web Service → AWS ECS/EC2
- Render PostgreSQL → AWS RDS
- Render Workers → AWS ECS Tasks
- Render Redis → AWS ElastiCache

---

## Testing Patterns

### Backend Testing

- **Unit Tests:** Service methods, calculations
- **Integration Tests:** API endpoints, database operations
- **Performance Tests:** Query optimization, load testing

### Frontend Testing

- **Component Tests:** Render, user interactions
- **Integration Tests:** API integration, data flow
- **Manual Testing:** User acceptance testing

---

## Key Architectural Decisions

1. **Async Processing:** All session processing happens asynchronously
2. **Denormalized Scores:** Pre-calculate and store scores for performance
3. **Polling vs WebSockets:** Polling for MVP (simpler), WebSockets for future
4. **Simple API Auth:** API key for MVP, JWT for production
5. **Render for MVP:** Fast deployment, AWS for production scale

---

## Design Principles

1. **Separation of Concerns:** Clear boundaries between layers
2. **Single Responsibility:** Each component has one job
3. **DRY (Don't Repeat Yourself):** Reusable components and services
4. **Scalability:** Design for growth (3K → 10K+ sessions/day)
5. **Maintainability:** Clean code, good documentation
6. **Production-Ready:** Code quality suitable for production

---

## Future Patterns (Post-MVP)

- **AI Integration:** OpenAI API for pattern analysis
- **Predictive Models:** ML models for no-show prediction
- **Real-Time Updates:** WebSocket connections
- **Advanced Analytics:** Complex queries and aggregations
- **Microservices:** Potential service splitting at scale

