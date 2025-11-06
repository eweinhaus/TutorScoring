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
6. **students** - Student profiles with preferences (for matching service)
7. **match_predictions** - Pre-calculated match predictions (many-to-many relationship)

### Relationship Pattern

```
tutors (1) ──< (many) sessions
sessions (1) ──< (0 or 1) reschedules
tutors (1) ──< (1) tutor_scores
sessions (1) ──< (0 or 1) email_reports
students (1) ──< (many) match_predictions
tutors (1) ──< (many) match_predictions
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

**Session Endpoints:**
- **POST /api/sessions** - Session ingestion (async, returns 202) ✅
  - Requires X-API-Key header
  - Validates session data
  - Creates session and reschedule if needed
  - Queues Celery task for processing

**Tutor Endpoints:**
- **GET /api/tutors** - List tutors with filters/sorting ✅
  - Query params: risk_status, sort_by, sort_order, limit, offset
  - Returns paginated list with scores
  
- **GET /api/tutors/{id}** - Tutor detail ✅
  - Returns tutor with scores and statistics
  - Includes reschedule rates (7d, 30d, 90d)
  
- **GET /api/tutors/{id}/history** - Reschedule history ✅
  - Returns reschedule events and weekly trends
  - Query params: days, limit

**Health Endpoint:**
- **GET /api/health** - Health check ✅
  - Returns database and Redis connection status

**Matching Endpoints (Planned):**
- **GET /api/matching/students** - List all students
- **GET /api/matching/students/{id}** - Get student details
- **POST /api/matching/students** - Create student
- **GET /api/matching/tutors** - List tutors with preferences
- **GET /api/matching/tutors/{id}** - Get tutor details with preferences
- **PATCH /api/matching/tutors/{id}** - Update tutor preferences
- **GET /api/matching/predict/{student_id}/{tutor_id}** - Get match prediction
- **POST /api/matching/generate-all** - Generate all predictions (batch)
- **GET /api/matching/students/{id}/matches** - Get all matches for student
- **GET /api/matching/tutors/{id}/matches** - Get all matches for tutor

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

**API Key Configuration:**
- **Backend:** Reads `API_KEY` from `backend/.env` or environment variables
- **Frontend:** Reads `VITE_API_KEY` from `frontend/.env` or environment variables
- **Critical:** Both must match exactly or API calls will return 401 Unauthorized
- **Location:**
  - Backend: `backend/.env` → `API_KEY=...`
  - Frontend: `frontend/.env` → `VITE_API_KEY=...`
- **Frontend Services:**
  - Main API: `frontend/src/services/api.js` uses `import.meta.env.VITE_API_KEY`
  - Matching API: `frontend/src/services/matchingApi.js` uses `import.meta.env.VITE_API_KEY`
- **Troubleshooting 401 Errors:**
  1. Check backend API key: `cd backend && source venv/bin/activate && python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('API_KEY'))"`
  2. Check frontend API key: `cat frontend/.env | grep VITE_API_KEY`
  3. Ensure they match exactly
  4. Update frontend `.env` if needed: `VITE_API_KEY=<backend-api-key>`
  5. **Restart frontend dev server** (Vite only reads `.env` at startup)
  6. Verify: Check browser console for API key length log: `[API] API key configured (length: X)`

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

### AWS Deployment (Complete)

**Infrastructure:**
- **Frontend:** S3 bucket → CloudFront CDN → HTTPS endpoint
- **API:** ECS Fargate → Application Load Balancer → CloudFront `/api/*` proxy
- **Worker:** ECS Fargate (background tasks)
- **Database:** RDS PostgreSQL 14.19 (private subnet)
- **Cache/Queue:** ElastiCache Redis (private subnet)
- **Secrets:** AWS Secrets Manager
- **Container Registry:** ECR (Elastic Container Registry)

**Network Architecture:**
- VPC with public/private subnets (or default VPC with fallback)
- Security groups for service isolation
- Internal service communication via private subnets
- NAT Gateway for outbound access (optional, uses public subnets if limit reached)
- Application Load Balancer for public API access
- Internet Gateway for public internet access

**Deployment Automation:**
- Fully automated deployment scripts in `scripts/aws_deploy/`
- Idempotent scripts (can run multiple times safely)
- Prerequisites checking and installation
- Error handling for AWS service limits
- Secrets management with late prompting
- CloudFront cache invalidation

**Key Patterns:**
- **Relative URLs:** Frontend uses `/api/*` (relative) to avoid mixed content
- **CloudFront Proxy:** Cache behavior routes `/api/*` to ALB origin
- **Docker Platform:** Build with `--platform linux/amd64` for ECS Fargate
- **Service Limits:** Fallback to default VPC/subnets if limits reached
- **Health Checks:** ALB health checks on `/api/health` endpoint
- **Task Registration:** ECS tasks automatically register with ALB target groups

**Security:**
- AWS Secrets Manager for sensitive variables (vs. Render dashboard)
- IAM roles for service permissions (ECS task execution role)
- SSL/TLS via CloudFront (HTTPS for all traffic)
- VPC security groups for network isolation
- CloudWatch for monitoring and logging
- S3 bucket policies for public read access
- CORS configured for CloudFront origin only

**Frontend Deployment Pattern:**
```
1. Build frontend (npm run build)
2. Sync to S3 (aws s3 sync dist/ s3://bucket)
3. Invalidate CloudFront cache (aws cloudfront create-invalidation)
4. Wait 2-3 minutes for propagation
```

**API Deployment Pattern:**
```
1. Build Docker image (--platform linux/amd64)
2. Push to ECR (docker push)
3. Update ECS service (force-new-deployment)
4. Wait for task to become healthy
5. Verify ALB target health
```

### Render Deployment (Partial - Historical)

**Infrastructure Mapping:**
- Render Web Service → AWS ECS Fargate or EC2
- Render PostgreSQL → AWS RDS (Multi-AZ for production)
- Render Workers → AWS ECS Tasks or EC2
- Render Redis (Key Value) → AWS ElastiCache for Redis
- Render Static Site → S3 + CloudFront

**Architecture Preservation:**
- Same FastAPI application code (no changes)
- Same database schema (Alembic migrations reusable)
- Same Celery worker configuration
- Same environment variable structure
- Update connection strings and service endpoints

**Network Architecture:**
- VPC with public/private subnets
- Security groups for service isolation
- Internal service communication via private subnets
- NAT Gateway for outbound access
- Application Load Balancer for public API access

**Security Enhancements:**
- AWS Secrets Manager for sensitive variables (vs. Render dashboard)
- IAM roles for service permissions
- SSL/TLS via ACM
- VPC security groups for network isolation
- CloudWatch for monitoring and logging

---

## Testing Patterns

### Backend Testing

- **Unit Tests:** Service methods, calculations ✅
- **Integration Tests:** API endpoints, database operations ✅
- **Performance Tests:** Query optimization, load testing
- **TestClient:** Uses FastAPI TestClient with httpx 0.27.2 (pinned for Starlette compatibility) ✅
- **Status:** 91/96 tests passing (94.8%), 17/18 API tests passing (94.4%)

### Frontend Testing

- **E2E Tests:** Playwright tests for full user flows ✅
- **Component Tests:** Render, user interactions
- **Integration Tests:** API integration, data flow ✅
- **Manual Testing:** User acceptance testing
- **Status:** 16/16 E2E tests passing (100%) ✅

### Test Selector Best Practices

**E2E Test Patterns:**
- Use specific, semantic selectors (avoid generic `svg`, `div`, etc.)
- Target component sections before selecting elements within
- Use Recharts-specific classes (`recharts-surface`) for chart elements
- Example: `chartSection.locator('svg.recharts-surface')` not `page.locator('svg').first()`

### API Parameter Naming Convention

**Important Pattern:** Frontend constants must match backend API expectations exactly:
- Backend expects: `reschedule_rate_30d`, `total_sessions_30d`
- Frontend constants in `utils/constants.js` must use these exact names
- Mismatch causes 400 Bad Request errors

### Component Error Handling Pattern

**Defensive Programming for API Data:**
- API may return string numbers (e.g., `"80.00"`) or null values
- Components must safely parse and validate all values
- Use try-catch blocks around risky operations
- Normalize data before passing to child components
- Example: RiskBadge component handles string/number/null/undefined safely

### Dependency Version Management

**Critical Version Pins:**
- **httpx==0.27.2** - Required for Starlette 0.27.0 TestClient compatibility
  - httpx 0.28.1+ introduces breaking changes (removes `app` parameter)
  - TestClient fixture fails with newer httpx versions
  - Always pin httpx to compatible version in requirements.txt

### Matching Service Data Generation

**Script:** `scripts/generate_matching_data.py`
- **Usage:** `python scripts/generate_matching_data.py --num-students 20`
- **Functions:**
  - `generate_students()` - Creates student profiles with preferences
  - `enhance_tutors()` - Adds matching preferences to existing tutors
  - `generate_predictions()` - Creates match predictions for all student-tutor pairs
- **Important Notes:**
  - Uses `db.add_all()` not `bulk_save_objects()` for proper session management
  - No need to import `get_tutor_stats` (builds tutor_stats manually from `tutor.tutor_score`)
  - ML model warnings are expected if xgboost not installed (uses rule-based fallback)
- **Troubleshooting:**
  - If import error: Check `app/services/tutor_service.py` for actual function names
  - If session error: Ensure using `db.add_all()` followed by `db.commit()` and `db.refresh()`
  - If no students: Run `python scripts/generate_matching_data.py --num-students 20`

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

## Matching Service Patterns

### Matching Service Architecture

**Components:**
- **Student Model:** Stores student preferences and demographics
- **Tutor Extension:** Adds matching preferences to existing tutor model
- **Match Prediction Model:** Pre-calculated predictions for all student-tutor pairs
- **ML Model:** XGBoost binary classifier for churn prediction
- **AI Explanation Service:** GPT-4 generates natural language explanations

### Matching Data Flow

```
1. Generate Students & Enhance Tutors
   ↓
2. Calculate Features for All Pairs
   ↓
3. Run ML Model Predictions
   ↓
4. Store Predictions in Database
   ↓
5. User Selects Student & Tutor
   ↓
6. Fetch Match Prediction
   ↓
7. Generate AI Explanation (on-demand)
   ↓
8. Display Match Details
```

### Feature Engineering Pattern

**Mismatch Scores (Key Predictive Features):**
- `pace_mismatch`: |student.preferred_pace - tutor.preferred_pace|
- `style_mismatch`: Distance metric between teaching styles
- `communication_mismatch`: |student.communication - tutor.communication|
- `age_difference`: |student.age - tutor.age|

**Compatibility Score:**
- Weighted inverse of mismatch scores
- Normalized to 0-1 scale
- Higher score = better match

### ML Model Pattern

**Pre-calculation Strategy:**
- Generate predictions for all student-tutor combinations upfront
- Store in `match_predictions` table
- Fast API responses (no real-time computation)
- Update when preferences change

**Risk Level Thresholds:**
- Configurable thresholds (default: Low < 0.3, Medium 0.3-0.7, High ≥ 0.7)
- Stored in environment variables for flexibility

### AI Explanation Pattern

**On-Demand Generation:**
- Generate explanations when user requests match details
- Cache similar explanations to reduce API calls
- Use GPT-4 Turbo for cost efficiency
- Fallback to rule-based explanation if API fails

**Prompt Structure:**
- Include student profile, tutor profile, match metrics
- Request 2-3 sentence explanation
- Highlight specific compatibility factors

### Matching Dashboard Pattern

**Two-Column Layout:**
- Students (left) | Tutors (right)
- Clickable cards for selection
- Inline match detail panel when both selected
- Visual indicators for risk levels (color-coded)

**Visual Design:**
- Risk badges: Green (low), Yellow (medium), Red (high)
- Compatibility score: Progress bar (0-100%)
- Mismatch indicators: Horizontal bars with severity
- AI explanation: Highlighted card

---

## Future Patterns (Post-MVP)

- **AI Integration:** OpenAI API for pattern analysis ✅ (implemented in matching service)
- **Predictive Models:** ML models for no-show prediction
- **Real-Time Updates:** WebSocket connections
- **Advanced Analytics:** Complex queries and aggregations
- **Microservices:** Potential service splitting at scale

