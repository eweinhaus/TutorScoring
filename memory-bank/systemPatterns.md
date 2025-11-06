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
8. **session_reschedule_predictions** - ML predictions for upcoming sessions (one-to-one with sessions)

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

**Matching Endpoints:** ✅ Implemented
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

**Upcoming Sessions Endpoints:** ✅ Implemented
- **GET /api/upcoming-sessions** - List upcoming sessions with reschedule predictions
- **POST /api/upcoming-sessions/batch-predict** - Generate predictions for multiple sessions
- **POST /api/upcoming-sessions/{session_id}/refresh** - Refresh prediction for specific session

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

### XGBoost ML Model Workflow

**Model Type:** XGBoost Binary Classifier (XGBClassifier)  
**Purpose:** Predict churn probability (0-1) for student-tutor matches  
**Location:** `backend/app/services/match_prediction_service.py`  
**Training Script:** `scripts/train_match_model.py`

#### Model Training Workflow

**Training Process (`train_match_model.py`):**
1. **Generate Synthetic Training Data:**
   - Creates 1000+ synthetic student-tutor pairs
   - Uses realistic churn distribution (~12% churn rate)
   - Generates features using `extract_features()` from feature_engineering service
   - Labels: binary (0=no churn, 1=churn) based on compatibility threshold

2. **Data Split:**
   - 80/20 train/test split with stratification
   - Random state: 42 (reproducible)

3. **Model Configuration:**
   - Algorithm: XGBoost (XGBClassifier)
   - Hyperparameters:
     - `n_estimators=100` (number of trees)
     - `max_depth=5` (tree depth limit)
     - `learning_rate=0.1` (shrinkage)
     - `random_state=42` (reproducibility)
     - `eval_metric='logloss'` (evaluation metric)
   - Class imbalance handling:
     - `scale_pos_weight` = ratio of negative to positive samples
     - `sample_weight` = 'balanced' weights applied during training

4. **Training:**
   - Model trained with sample weights to handle class imbalance
   - Target precision: >70%

5. **Evaluation:**
   - Metrics calculated: accuracy, precision, recall, F1-score, ROC-AUC
   - Feature importance extracted and displayed (top 10 features)

6. **Model Persistence:**
   - Model saved to: `backend/models/match_model.pkl` (joblib format)
   - Feature names saved to: `backend/models/feature_names.json`
   - Metadata saved to: `backend/models/model_metadata.json`:
     - Model version (v1.0)
     - Training timestamp
     - Performance metrics
     - Feature count

#### Feature Engineering Workflow

**Feature Extraction (`feature_engineering.py`):**

**Total Features: 17 features**

1. **Mismatch Scores (4 features):**
   - `pace_mismatch`: |student.preferred_pace - tutor.preferred_pace| (0-4 scale)
   - `style_mismatch`: Binary (0=match, 1=mismatch) based on teaching style match
   - `communication_mismatch`: |student.communication_style_preference - tutor.communication_style| (0-4 scale)
   - `age_difference`: |student.age - tutor.age| (absolute difference)

2. **Student Features (5 features):**
   - `student_age`: Student age (default: 15.0 if missing)
   - `student_pace`: Student preferred pace (1-5, default: 3.0)
   - `student_urgency`: Urgency level (1-5, default: 3.0)
   - `student_experience`: Previous tutoring experience count (default: 0.0)
   - `student_satisfaction`: Previous satisfaction rating (1-5, default: 3.0)

3. **Tutor Features (4 features):**
   - `tutor_age`: Tutor age (default: 30.0 if missing)
   - `tutor_experience`: Experience years (default: 2.0)
   - `tutor_confidence`: Confidence level (1-5, default: 3.0)
   - `tutor_pace`: Tutor preferred pace (1-5, default: 3.0)

4. **Tutor Statistics (3 features, optional):**
   - `tutor_reschedule_rate_30d`: Reschedule rate over 30 days (0.0-1.0)
   - `tutor_total_sessions_30d`: Total sessions in last 30 days
   - `tutor_is_high_risk`: Binary flag (1.0 if high risk, 0.0 otherwise)

5. **Derived Feature (1 feature):**
   - `compatibility_score`: Weighted compatibility score (0-1) calculated from mismatch scores

**Feature Calculation:**
- `calculate_mismatch_scores()`: Computes 4 mismatch metrics
- `calculate_compatibility_score()`: Converts mismatches to 0-1 compatibility score
- `extract_features()`: Combines all features into feature vector in consistent order

#### Prediction Workflow

**Prediction Process (`match_prediction_service.py`):**

1. **Model Loading (Cached):**
   - Function: `load_model()`
   - First call: Loads model from disk (`backend/models/match_model.pkl`)
   - Caches model, feature names, and metadata in memory
   - Subsequent calls: Returns cached model (no disk I/O)
   - Error handling: Raises `FileNotFoundError` if model not found, `ImportError` if ML libraries missing

2. **Feature Extraction:**
   - Function: `extract_features(student, tutor, tutor_stats)`
   - Extracts all 17 features for the student-tutor pair
   - Returns dictionary of feature name → value

3. **Feature Vector Construction:**
   - Ensures features are in correct order (matching training order)
   - Uses `feature_names.json` to order features correctly
   - Creates numpy array: `np.array([[feature_values]])`

4. **Churn Probability Prediction:**
   - Function: `predict_churn_risk(student, tutor, tutor_stats)`
   - Calls `model.predict_proba(feature_vector)[0, 1]`
   - Returns probability of churn (class 1) as float (0-1)

5. **Risk Level Determination:**
   - Function: `determine_risk_level(probability, low_threshold=0.3, high_threshold=0.7)`
   - Thresholds configurable via environment variables:
     - `MATCH_RISK_THRESHOLD_LOW` (default: 0.3)
     - `MATCH_RISK_THRESHOLD_HIGH` (default: 0.7)
   - Returns: 'low', 'medium', or 'high'

6. **Full Match Prediction:**
   - Function: `predict_match(student, tutor, tutor_stats)`
   - Returns dictionary with:
     - `churn_probability`: float (0-1)
     - `risk_level`: str ('low', 'medium', 'high')
     - `compatibility_score`: float (0-1)
     - `mismatch_scores`: dict with pace, style, communication, age differences

#### Fallback Mechanism

**Rule-Based Fallback:**
- Triggered when:
  - Model file not found (`FileNotFoundError`)
  - ML libraries not installed (`ImportError`)
- Fallback logic:
  1. Calculate mismatch scores using `calculate_mismatch_scores()`
  2. Calculate compatibility score using `calculate_compatibility_score()`
  3. Churn probability = 1.0 - compatibility_score
  4. Risk level determined from churn probability
- Service continues to work without trained model (graceful degradation)

#### Model Storage and Files

**Directory:** `backend/models/`

**Files:**
1. `match_model.pkl`: Trained XGBoost model (joblib format)
2. `feature_names.json`: Ordered list of feature names (JSON array)
3. `model_metadata.json`: Model metadata including:
   - `model_version`: Version string (e.g., 'v1.0')
   - `trained_at`: ISO timestamp of training
   - `metrics`: Performance metrics (accuracy, precision, recall, F1, ROC-AUC)
   - `feature_count`: Number of features

#### Model Usage in API

**Prediction Endpoints:**
- `GET /api/matching/predict/{student_id}/{tutor_id}`: Get or create match prediction
- `POST /api/matching/generate-all`: Batch generate predictions for all pairs

**Database Storage:**
- Predictions stored in `match_predictions` table via `get_or_create_match_prediction()`
- Pre-calculated predictions for fast API responses
- Unique constraint on (student_id, tutor_id) prevents duplicates

**Performance:**
- Model loading: Cached in memory (first load ~100-200ms, subsequent loads ~0ms)
- Prediction time: <10ms per prediction (in-memory model)
- Batch generation: ~100 predictions/second

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

## Reschedule Prediction Patterns

### Reschedule Prediction Service Architecture

**Components:**
- **SessionReschedulePrediction Model:** Stores ML predictions for upcoming sessions
- **Feature Engineering Service:** Extracts features from sessions and tutor history
- **ML Model:** XGBoost binary classifier for reschedule probability prediction
- **Prediction Service:** Generates predictions with fallback logic

### Reschedule Prediction Data Flow

```
1. Upcoming Session Created
   ↓
2. Feature Engineering (tutor history, temporal features, session context)
   ↓
3. ML Model Prediction (XGBoost)
   ↓
4. Risk Level Classification (low/medium/high)
   ↓
5. Store Prediction in Database
   ↓
6. Dashboard Displays Predictions
   ↓
7. Administrator Views High-Risk Sessions
   ↓
8. Early Intervention (emails, reminders)
```

### Feature Engineering Pattern

**Feature Categories (Total: ~15 features):**

1. **Tutor History Features (9 features):**
   - `tutor_reschedule_rate_7d, 30d, 90d`: Reschedule rates (0-1, converted from percentage)
   - `tutor_total_sessions_7d, 30d, 90d`: Total sessions in time windows
   - `tutor_is_high_risk`: Binary flag (1.0 if high risk, 0.0 otherwise)
   - `tutor_reschedule_trend`: Trend indicator (-1 to 1, comparing 7d vs 30d rates)

2. **Temporal Features (6 features):**
   - `day_of_week`: 0=Monday, 6=Sunday
   - `hour_of_day`: 0-23
   - `time_of_day_category`: 0=morning, 1=afternoon, 2=evening, 3=night
   - `is_weekend`: Binary (1.0 if weekend, 0.0 otherwise)
   - `days_until_session`: Days until scheduled session
   - `hours_until_session`: Hours until scheduled session

3. **Session Context Features (optional):**
   - `session_duration_minutes`: Duration of session
   - Future: student history, subject area, etc.

### ML Model Pattern (XGBoost)

**Model Type:** XGBoost Binary Classifier (XGBClassifier)  
**Purpose:** Predict reschedule probability (0-1) for upcoming sessions  
**Location:** `backend/app/services/reschedule_prediction_service.py`  
**Training Script:** `scripts/train_reschedule_model.py`

#### Model Training Workflow

**Training Process (`train_reschedule_model.py`):**
1. **Extract Historical Training Data:**
   - Uses completed sessions with reschedule history
   - Requires minimum sessions per tutor (default: 500)
   - Generates features using `extract_features()` from feature engineering service
   - Labels: binary (0=no reschedule, 1=reschedule)

2. **Model Configuration:**
   - Algorithm: XGBoost (XGBClassifier)
   - Hyperparameters:
     - `n_estimators=100` (number of trees)
     - `max_depth=5` (tree depth limit) - **⚠️ Currently too high, causing overfitting**
     - `learning_rate=0.1` (shrinkage)
     - `random_state=42` (reproducibility)
   - Class imbalance handling:
     - `scale_pos_weight` = ratio of negative to positive samples
     - `sample_weight` = 'balanced' weights

3. **Model Persistence:**
   - Model saved to: `backend/models/reschedule_model.pkl` (joblib format)
   - Feature names saved to: `backend/models/reschedule_feature_names.json`
   - Metadata saved to: `backend/models/reschedule_model_metadata.json`

#### Known Model Issues

**Current Problems:**
- ⚠️ **Severe Feature Scaling Mismatch:** Features not normalized (hours_until_session: 296.93 vs tutor_reschedule_rate_30d: 0.15)
- ⚠️ **Extreme Overfitting:** 99.16% accuracy, 100% recall suggests memorization
- ⚠️ **Single Feature Dominance:** 93.64% importance on `session_duration_minutes`
- ⚠️ **Miscalibrated Predictions:** Predicts 0.1-2.4% (mean: 1.01%) when training data had 15.3% reschedule rate
- ⚠️ **All Low Risk:** 100% of predictions categorized as "low" risk

**Recommended Fixes:**
1. **Feature Scaling:** Use StandardScaler or MinMaxScaler for all features
2. **Reduce Overfitting:** 
   - Reduce `max_depth` from 5 to 3-4
   - Add early stopping
   - Increase regularization (higher `min_child_weight`, `gamma`)
   - Use cross-validation
3. **Recalibration:** Use Platt scaling or isotonic regression to calibrate probabilities
4. **Feature Engineering:** Investigate why `session_duration_minutes` dominates, consider feature engineering alternatives

#### Prediction Workflow

**Prediction Process (`reschedule_prediction_service.py`):**

1. **Model Loading (Cached):**
   - Function: `load_model()`
   - First call: Loads model from disk (`backend/models/reschedule_model.pkl`)
   - Caches model, feature names, and metadata in memory
   - Subsequent calls: Returns cached model (no disk I/O)
   - Error handling: Falls back to rule-based prediction if model not found

2. **Feature Extraction:**
   - Function: `extract_features(session, tutor_stats, db)`
   - Extracts all features for the session
   - Returns dictionary of feature name → value

3. **Feature Vector Construction:**
   - Ensures features are in correct order (matching training order)
   - Uses `reschedule_feature_names.json` to order features correctly
   - Creates numpy array: `np.array([[feature_values]])`

4. **Reschedule Probability Prediction:**
   - Function: `predict_reschedule_probability(session, tutor_stats, db)`
   - Calls `model.predict_proba(feature_vector)[0, 1]`
   - Returns probability of reschedule (class 1) as float (0-1)

5. **Risk Level Determination:**
   - Function: `determine_risk_level(probability, low_threshold=0.15, high_threshold=0.35)`
   - Thresholds configurable (defaults: low < 15%, medium < 35%, high >= 35%)
   - Returns: 'low', 'medium', or 'high'

6. **Full Prediction:**
   - Function: `predict_session_reschedule(session, tutor_stats, db)`
   - Returns dictionary with:
     - `reschedule_probability`: float (0-1)
     - `risk_level`: str ('low', 'medium', 'high')
     - `features`: Dict (for debugging)
     - `model_version`: str

#### Fallback Mechanism

**Rule-Based Fallback:**
- Triggered when:
  - Model file not found (`FileNotFoundError`)
  - ML libraries not installed (`ImportError`)
- Fallback logic:
  1. Use tutor's reschedule rate as fallback
  2. `rate_30d = tutor_stats.get('reschedule_rate_30d', 0.0)`
  3. Return `float(rate_30d) / 100.0` if available, else 0.1
- Service continues to work without trained model (graceful degradation)

### Upcoming Sessions Dashboard Pattern

**Three-Column Table Layout:**
- Session details (tutor name, student ID, scheduled time)
- Reschedule probability (percentage with color-coded risk badge)
- Actions (refresh prediction, view details)

**Filtering & Sorting:**
- Filter by: risk level (low/medium/high), tutor ID, date range (days_ahead)
- Sort by: scheduled_time, reschedule_probability, tutor_name, student_id
- Pagination: Default 50 sessions per page, configurable limit

**Real-Time Updates:**
- React Query polling: 30-second intervals (same as existing dashboard)
- Automatic refresh as sessions approach
- Filter out past sessions on backend

**API Endpoints:**
- `GET /api/upcoming-sessions`: List upcoming sessions with predictions
- `POST /api/upcoming-sessions/batch-predict`: Generate predictions for multiple sessions
- `POST /api/upcoming-sessions/{session_id}/refresh`: Refresh prediction for specific session

### Database Storage Pattern

**SessionReschedulePrediction Model:**
- **One-to-one relationship** with Session model (`session_id` unique)
- Stores: `reschedule_probability` (Numeric 0-1), `risk_level` (low/medium/high), `model_version`, `predicted_at`, `features_json`
- Indexes: session_id, risk_level, predicted_at, composite (session_id, risk_level)

**Pre-calculation Strategy:**
- Predictions generated when sessions are created or on-demand
- Stored in database for fast retrieval
- Updated when features change (e.g., tutor reschedule rate updates)
- Batch prediction available for bulk updates

---

## Future Patterns (Post-MVP)

- **AI Integration:** OpenAI API for pattern analysis ✅ (implemented in matching service)
- **Predictive Models:** ML models for no-show prediction
- **Real-Time Updates:** WebSocket connections
- **Advanced Analytics:** Complex queries and aggregations
- **Microservices:** Potential service splitting at scale

