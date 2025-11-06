# Technical Context
## Tutor Quality Scoring System

---

## Technology Stack

### Backend Stack

**API Framework:**
- **FastAPI** (Python 3.11+) - Modern, fast async web framework
- **Uvicorn** - ASGI server for FastAPI
- **Pydantic** - Data validation and settings management

**Database:**
- **PostgreSQL** 14+ - Primary relational database
- **SQLAlchemy** 2.0+ - ORM for database operations
- **Alembic** - Database migration tool

**Task Queue:**
- **Celery** 5.3+ - Distributed task queue
- **Redis** 7+ - Message broker and result backend

**Email Service:**
- **SendGrid** (MVP primary) - Email delivery service
- **AWS SES** (Alternative) - Email service via AWS

**Python Dependencies:**
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.9
celery==5.3.4
redis==5.0.1
sendgrid==6.11.0
python-dotenv==1.0.0
pydantic==2.5.0
httpx==0.27.2  # Pinned for Starlette TestClient compatibility
```

**ML Dependencies (Optional - for Matching Service):**
```
xgboost>=2.0.0  # XGBoost binary classifier for churn prediction
scikit-learn>=1.3.0  # Model evaluation and utilities
pandas>=2.0.0  # Data manipulation (training script)
numpy>=1.24.0  # Numerical operations
joblib>=1.3.0  # Model serialization
faker>=19.0.0  # Synthetic data generation (training script)
```
**Note:** ML libraries are optional. The matching service works with rule-based fallback if ML libraries are not installed or model is not trained.

### Frontend Stack

**Framework:**
- **React** 18+ - UI framework
- **React Router** 6+ - Routing
- **Vite** - Build tool and dev server

**Data Fetching:**
- **@tanstack/react-query** - Server state management
- **Axios** - HTTP client

**Visualization:**
- **Recharts** - Chart library for React

**Styling:**
- **Tailwind CSS** (Recommended) - Utility-first CSS framework
- **CSS Modules** (Alternative) - Scoped CSS

**Development Tools:**
- **ESLint** - Code linting
- **Prettier** - Code formatting

### Infrastructure (MVP)

**Deployment Platform:**
- **Render** - Cloud platform for MVP
  - Web Service: FastAPI application
  - Background Worker: Celery workers
  - PostgreSQL: Managed database
  - Redis: Managed Redis instance
  - Static Site: Frontend dashboard

**Future Infrastructure (Production):**
- **AWS** - Production cloud platform
  - ECS/EC2: Compute services
  - RDS: Managed PostgreSQL
  - ElastiCache: Managed Redis
  - S3: Static site hosting
  - CloudFront: CDN

---

## Development Environment

### Local Setup Requirements

**Required Software:**
- Python 3.11+ (recommended: 3.11 or 3.12)
  - **Current:** Python 3.9.6 installed (upgrade recommended but not blocking)
- Node.js 18+ (LTS recommended)
- PostgreSQL 14+ (local or Docker)
  - **Current:** PostgreSQL 14.19 installed via Homebrew, running on port 5432
- Redis 7+ (local or Docker)
  - **Current:** Redis 8.2.3 installed via Homebrew, running on port 6379
- Git
  - **Current:** Git repository initialized

**Development Tools:**
- Virtual environment (venv or poetry)
- Package managers: pip, npm
- Code editor (VS Code recommended)

### Environment Variables

**Backend (.env):**
```bash
DATABASE_URL=postgresql://user@localhost:5432/tutor_scoring
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
EMAIL_SERVICE=sendgrid
SENDGRID_API_KEY=your_sendgrid_api_key_here
ADMIN_EMAIL=admin@example.com
SECRET_KEY=your-secret-key-here-change-in-production
API_KEY=your-api-key-here-change-in-production
ENVIRONMENT=development
```

**Current Configuration:**
- Database: `tutor_scoring` created and accessible
- Connection strings: Configured in backend/.env
- Services: PostgreSQL and Redis running via Homebrew services
- Virtual environment: Created in backend/venv/
- Alembic: Initialized and configured to use DATABASE_URL from environment

**Frontend (.env):**
```bash
VITE_API_URL=http://localhost:8000
VITE_API_KEY=your-api-key
```

---

## Project Structure

```
TutorScoring/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── main.py         # FastAPI app
│   │   ├── api/            # API routes
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   ├── tasks/          # Celery tasks
│   │   └── utils/           # Utilities
│   ├── alembic/            # Migrations
│   ├── tests/              # Backend tests
│   └── requirements.txt    # Dependencies
│
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API client
│   │   ├── hooks/         # Custom hooks
│   │   └── utils/         # Utilities
│   ├── public/            # Static assets
│   └── package.json        # Dependencies
│
├── scripts/                # Utility scripts
│   ├── generate_data.py   # Synthetic data generator
│   └── setup_db.py        # Database setup
│
├── planning/               # Documentation
│   ├── PRD_MVP.md
│   ├── PRDs/              # Sub-PRDs
│   ├── architecture/      # Architecture docs
│   └── roadmap.md
│
├── memory-bank/            # Memory bank files
│   ├── projectbrief.md
│   ├── productContext.md
│   ├── activeContext.md
│   ├── systemPatterns.md
│   ├── techContext.md
│   └── progress.md
│
└── README.md
```

---

## Database Schema

### Core Tables

**tutors:**
- id (UUID, PK)
- name (VARCHAR)
- email (VARCHAR, unique)
- created_at, updated_at (TIMESTAMP)
- is_active (BOOLEAN)

**sessions:**
- id (UUID, PK)
- tutor_id (UUID, FK → tutors)
- student_id (VARCHAR)
- scheduled_time, completed_time (TIMESTAMP)
- status (VARCHAR: completed/rescheduled/no_show)
- duration_minutes (INTEGER)
- created_at, updated_at (TIMESTAMP)

**reschedules:**
- id (UUID, PK)
- session_id (UUID, FK → sessions, unique)
- initiator (VARCHAR: tutor/student)
- original_time, new_time (TIMESTAMP)
- reason, reason_code (TEXT, VARCHAR)
- cancelled_at (TIMESTAMP)
- hours_before_session (DECIMAL)
- created_at (TIMESTAMP)

**tutor_scores:**
- id (UUID, PK)
- tutor_id (UUID, FK → tutors, unique)
- reschedule_rate_7d, 30d, 90d (DECIMAL)
- total_sessions_7d, 30d, 90d (INTEGER)
- tutor_reschedules_7d, 30d, 90d (INTEGER)
- is_high_risk (BOOLEAN)
- risk_threshold (DECIMAL)
- last_calculated_at, created_at, updated_at (TIMESTAMP)

**email_reports:**
- id (UUID, PK)
- session_id (UUID, FK → sessions)
- recipient_email (VARCHAR)
- sent_at (TIMESTAMP)
- status (VARCHAR: sent/failed/pending)
- error_message (TEXT)
- created_at (TIMESTAMP)

**session_reschedule_predictions:**
- id (UUID, PK)
- session_id (UUID, FK → sessions, unique)
- reschedule_probability (NUMERIC 5,4: 0.0000 to 1.0000)
- risk_level (VARCHAR: low/medium/high)
- model_version (VARCHAR)
- predicted_at (TIMESTAMP)
- features_json (JSON)
- created_at, updated_at (TIMESTAMP)

---

## API Endpoints (Implemented)

### Session Endpoints ✅

**POST /api/sessions**
- Ingest session data
- Returns: 202 Accepted (async processing)
- Body: Session data with reschedule info
- Requires: X-API-Key header
- Status: ✅ Implemented and working

### Tutor Endpoints ✅

**GET /api/tutors**
- List tutors with scores
- Query params: risk_status, sort_by, sort_order, limit, offset
- Returns: List of tutors with pagination
- Status: ✅ Implemented and working

**GET /api/tutors/{id}**
- Get tutor details
- Returns: Tutor with scores and statistics
- Status: ✅ Implemented and working

**GET /api/tutors/{id}/history**
- Get reschedule history
- Query params: days, limit
- Returns: Reschedule events and trends
- Status: ✅ Implemented and working

### Health Endpoint ✅

**GET /api/health**
- System health check
- Returns: Status of database, Redis, version
- Status: ✅ Implemented and working

### Upcoming Sessions Endpoints ✅

**GET /api/upcoming-sessions**
- List upcoming sessions with reschedule predictions
- Query params: days_ahead, risk_level, tutor_id, limit, offset, sort_by, sort_order
- Returns: Paginated list of upcoming sessions with predictions
- Status: ✅ Implemented and working

**POST /api/upcoming-sessions/batch-predict**
- Generate predictions for multiple sessions
- Body: session_ids (optional), days_ahead (optional)
- Returns: Batch prediction results
- Status: ✅ Implemented and working

**POST /api/upcoming-sessions/{session_id}/refresh**
- Refresh prediction for specific session
- Returns: Updated prediction
- Status: ✅ Implemented and working

---

## Background Processing (Implemented)

### Celery Configuration ✅

**Broker:** Redis ✅
**Result Backend:** Redis ✅
**Task Serialization:** JSON ✅
**Time Limits:** 5 min hard, 4 min soft ✅
**Location:** `backend/app/tasks/celery_app.py`

### Tasks ✅

**process_session(session_id)** ✅
- Process session completion
- Calculate reschedule rates
- Update tutor scores
- Queue email report task
- Retry: 3 attempts with exponential backoff
- Location: `backend/app/tasks/session_processor.py`

**send_email_report(session_id)** ✅
- Send email report
- Create EmailReport record
- Retry: 3 attempts with exponential backoff
- Location: `backend/app/tasks/email_tasks.py`

---

## Development Workflow

### Local Development

**Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```
**Status:** ✅ Currently running on http://localhost:8001

**Celery Worker:**
```bash
cd backend
celery -A app.tasks.celery_app worker --loglevel=info
```
**Status:** ✅ Ready to start (tasks implemented)

**Frontend:**
```bash
cd frontend
npm run dev
```
**Status:** ⏳ Not started (Next phase)

**Testing:**
```bash
cd backend
pytest tests/ -v
```
**Status:** ✅ 91/96 tests passing (94.8%)
- API Tests: ✅ 17/18 passing (94.4%)
- TestClient fixture: ✅ Fixed (httpx pinned to 0.27.2)

**Frontend E2E Tests:**
```bash
cd frontend
npm run test:e2e
```
**Status:** ✅ 16/16 tests passing (100%)

### Database Migrations

**Create Migration:**
```bash
cd backend
alembic revision --autogenerate -m "description"
```

**Apply Migration:**
```bash
alembic upgrade head
```

### Testing

**Backend:**
```bash
pytest backend/tests/
```

**Frontend:**
```bash
npm test  # If configured
```

---

## Deployment

### Render Deployment (Partial - Attempted)

**Status:** Partially deployed - API, Worker, Frontend, and Database are LIVE. Redis connection pending.

**Services Deployed:**
- ✅ **Web Service (API):** `tutor-scoring-api` - LIVE on https://tutor-scoring-api.onrender.com
- ✅ **Background Worker:** `tutor-scoring-worker` - LIVE (but Redis connection failing)
- ✅ **Static Site (Frontend):** `tutor-scoring-frontend` - LIVE on https://tutor-scoring-frontend.onrender.com
- ✅ **PostgreSQL:** `tutor-scoring-db` - LIVE, migrations completed
- ⚠️ **Redis (Key Value):** `tutor-scoring-redis` - Created, but connection strings not linked

**Build Commands:**
- Web Service: `cd backend && pip install -r requirements.txt`
- Start Command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Worker: `cd backend && celery -A app.tasks.celery_app worker --loglevel=info`
- Frontend: `cd frontend && npm install && npm run build`

**Python Version Compatibility:**
- Render uses Python 3.13 by default (not configurable via runtime.txt in backend/)
- Required dependency upgrades for Python 3.13:
  - `pydantic>=2.9.0` (pre-built wheels available)
  - `pydantic-settings>=2.6.0`
  - `sqlalchemy>=2.0.36` (Python 3.13 compatible)
  - `alembic>=1.14.0`
  - `psycopg2-binary>=2.9.10` (compiled for Python 3.13)

**Environment Variables (Render):**
- Set via Render dashboard (not MCP API for sensitive keys):
  - `DATABASE_URL` - Auto-linked from PostgreSQL service
  - `REDIS_URL` - Manual linking required (Key Value service internal connection string)
  - `CELERY_BROKER_URL` - Manual linking required
  - `CELERY_RESULT_BACKEND` - Manual linking required
  - `SENDGRID_API_KEY` - Manual entry (sensitive)
  - `API_KEY` - Manual entry (sensitive)
  - `SECRET_KEY` - Manual entry (sensitive)
  - `ADMIN_EMAIL` - Manual entry
  - `CORS_ORIGINS` - Comma-separated list of allowed origins

**Known Issues:**
- Redis connection strings cannot be programmatically linked via MCP API
- Internal Redis hostname (`red-*`) not resolving from services
- Manual dashboard linking required for Redis connection strings
- Test data seeding script needs DATABASE_URL from Render environment

**Lessons Learned:**
1. Render's Python 3.13 requires updated dependencies (pre-built wheels)
2. Redis Key Value service requires manual connection string linking in dashboard
3. CORS configuration should be dynamic from environment variables
4. Database migrations work seamlessly on Render PostgreSQL
5. Blueprint deployment creates all services but connection strings need manual configuration

### AWS Deployment (Planned)

**Infrastructure:**
- **PostgreSQL:** AWS RDS (managed service, Multi-AZ for production)
- **Redis:** AWS ElastiCache (managed service, Redis 7+)
- **API/Worker:** AWS ECS Fargate or EC2 (containerized deployment)
- **Frontend:** S3 + CloudFront (static hosting with CDN)

**Network Configuration:**
- VPC with public and private subnets
- Security groups for service-to-service communication
- NAT Gateway for outbound internet access
- Application Load Balancer for API service

**Security:**
- AWS Secrets Manager for sensitive environment variables
- IAM roles for service permissions
- SSL/TLS certificates via ACM
- WAF rules for API protection

**Deployment Strategy:**
- Use same application code (no changes needed)
- Update environment variables for AWS services
- Configure VPC networking for internal service communication
- Set up CloudWatch for monitoring and logging
- Use AWS CodePipeline for CI/CD (optional)

**Migration Path:**
- Same FastAPI application structure
- Same database schema (Alembic migrations)
- Same Celery worker configuration
- Update connection strings and environment variables

---

## Performance Targets

### API Performance
- Response time: <500ms (p95)
- Throughput: 3,000 sessions/day (~125/hour)
- Processing latency: <1 hour from session completion

### Frontend Performance
- Load time: <2 seconds
- Smooth interactions: 60fps
- Real-time updates: Poll every 30 seconds

### Database Performance
- Query optimization: Indexed columns
- Connection pooling: Configured in SQLAlchemy
- Caching: Redis cache for scores (5-minute TTL)

---

## Security Considerations

### MVP Security
- API key authentication
- Input validation (Pydantic)
- SQL injection prevention (SQLAlchemy ORM)
- CORS configuration

### Future Security
- JWT token authentication
- Data encryption at rest
- Rate limiting
- Audit logging
- HTTPS only (production)

---

## Dependencies Management

### Python
- Virtual environment isolation
- requirements.txt for dependencies
- Lock file (optional: poetry.lock)

### Node.js
- package.json for dependencies
- node_modules/ ignored in git
- package-lock.json for version locking

---

## External Services

### Required Services
- **SendGrid** (or AWS SES) - Email delivery
- **Render** - Hosting and infrastructure
- **GitHub** - Version control (assumed)

### Optional Services
- **OpenAI API** - Future AI features (Phase 2+)
- **Monitoring** - Application monitoring (future)

---

## Development Constraints

### Technical Constraints
- Python 3.11+ required
- Node.js 18+ required
- PostgreSQL 14+ required
- Redis 7+ required

### Business Constraints
- Must process 3,000 sessions/day
- Must deliver insights within 1 hour
- Must be demo-ready for interview
- Must show production-readiness

---

## Code Quality Standards

### Python
- Follow PEP 8 style guide
- Use type hints where possible
- Document functions with docstrings
- Black for code formatting
- Flake8 for linting

### JavaScript/React
- Follow React best practices
- Use functional components
- ESLint for linting
- Prettier for formatting

---

## Known Technical Decisions

1. **FastAPI over Django/Flask:** Modern async, fast, good for APIs
2. **Celery over RQ:** More features, better for production
3. **PostgreSQL over MySQL:** Better JSON support, ACID compliance
4. **React Query over Redux:** Simpler for server state, built-in caching
5. **Render over AWS for MVP:** Faster setup, easier deployment
6. **Tailwind over CSS Modules:** Faster development, better DX

---

## Future Technical Considerations

### Phase 2+
- OpenAI API integration for AI features
- ML models for predictive analytics
- Vector database for similarity search (optional)
- Advanced monitoring (Datadog, New Relic)

### Production
- AWS migration for scale
- Read replicas for database
- CDN for static assets
- Advanced caching strategies
- Auto-scaling configurations

