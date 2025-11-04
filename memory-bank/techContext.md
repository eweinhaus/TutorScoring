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
```

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
- Node.js 18+ (LTS recommended)
- PostgreSQL 14+ (local or Docker)
- Redis 7+ (local or Docker)
- Git

**Development Tools:**
- Virtual environment (venv or poetry)
- Package managers: pip, npm
- Code editor (VS Code recommended)

### Environment Variables

**Backend (.env):**
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/tutor_scoring
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
EMAIL_SERVICE=sendgrid
SENDGRID_API_KEY=your_key
ADMIN_EMAIL=admin@example.com
SECRET_KEY=your-secret-key
API_KEY=your-api-key
ENVIRONMENT=development
```

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

---

## API Endpoints

### Session Endpoints

**POST /api/sessions**
- Ingest session data
- Returns: 202 Accepted (async processing)
- Body: Session data with reschedule info

### Tutor Endpoints

**GET /api/tutors**
- List tutors with scores
- Query params: risk_status, sort_by, sort_order, limit, offset
- Returns: List of tutors with pagination

**GET /api/tutors/{id}**
- Get tutor details
- Returns: Tutor with scores and statistics

**GET /api/tutors/{id}/history**
- Get reschedule history
- Query params: days, limit
- Returns: Reschedule events and trends

### Health Endpoint

**GET /api/health**
- System health check
- Returns: Status of database, Redis, version

---

## Background Processing

### Celery Configuration

**Broker:** Redis
**Result Backend:** Redis
**Task Serialization:** JSON
**Time Limits:** 5 min hard, 4 min soft

### Tasks

**process_session(session_id)**
- Process session completion
- Calculate reschedule rates
- Update tutor scores
- Send email report
- Retry: 3 attempts with exponential backoff

---

## Development Workflow

### Local Development

**Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

**Celery Worker:**
```bash
cd backend
celery -A app.tasks.celery_app worker --loglevel=info
```

**Frontend:**
```bash
cd frontend
npm run dev
```

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

### Render Deployment

**Web Service:**
- Build: `pip install -r requirements.txt`
- Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

**Background Worker:**
- Build: `pip install -r requirements.txt`
- Start: `celery -A app.tasks.celery_app worker --loglevel=info`

**Static Site (Frontend):**
- Build: `cd frontend && npm install && npm run build`
- Publish: `frontend/dist`

### Environment Variables (Render)

Set via Render dashboard:
- Database URL (auto-provided from PostgreSQL service)
- Redis URL (auto-provided from Redis service)
- Email service credentials
- API keys
- Admin email

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

