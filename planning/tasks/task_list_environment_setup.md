# Task List: Environment Setup
## Tutor Quality Scoring System - MVP

**PRD Reference:** `planning/PRDs/PRD_Environment_Setup.md`  
**Status:** Not Started  
**Priority:** Critical (Foundation for all development)

---

## Overview

This task list covers the complete environment setup phase, including project structure creation, dependency installation, local service configuration, and deployment preparation. All tasks must be completed before proceeding to Data Foundation phase.

---

## Tasks

### 1. Project Structure Setup

#### 1.1 Create Root Directory Structure
- [ ] Create `backend/` directory
- [ ] Create `frontend/` directory
- [ ] Create `scripts/` directory
- [ ] Create `planning/` directory (already exists, verify structure)
- [ ] Verify directory structure matches PRD specification

#### 1.2 Initialize Git Repository
- [ ] Initialize git repository (if not already initialized)
- [ ] Create `.gitignore` file with comprehensive rules
- [ ] Add Python ignore patterns (__pycache__, venv/, *.pyc, etc.)
- [ ] Add Node.js ignore patterns (node_modules/, dist/, etc.)
- [ ] Add environment file patterns (.env, .env.local, etc.)
- [ ] Add IDE patterns (.vscode/, .idea/, etc.)
- [ ] Add OS patterns (.DS_Store, Thumbs.db, etc.)
- [ ] Add database files (*.db, *.sqlite)
- [ ] Add log files (*.log, logs/)
- [ ] Verify .gitignore is working correctly

---

### 2. Backend Environment Setup

#### 2.1 Python Environment
- [ ] Verify Python 3.11+ is installed
- [ ] Create Python virtual environment (`python -m venv venv`)
- [ ] Document activation commands for Mac/Linux and Windows
- [ ] Test virtual environment activation
- [ ] Add venv/ to .gitignore

#### 2.2 Backend Directory Structure
- [ ] Create `backend/app/` directory
- [ ] Create `backend/app/__init__.py`
- [ ] Create `backend/app/api/` directory
- [ ] Create `backend/app/models/` directory
- [ ] Create `backend/app/schemas/` directory
- [ ] Create `backend/app/services/` directory
- [ ] Create `backend/app/tasks/` directory
- [ ] Create `backend/app/utils/` directory
- [ ] Create `backend/app/middleware/` directory
- [ ] Create `backend/alembic/` directory (will be initialized by Alembic)
- [ ] Create `backend/tests/` directory
- [ ] Verify structure matches PRD specification

#### 2.3 Backend Dependencies
- [ ] Create `backend/requirements.txt` file
- [ ] Add FastAPI dependency (fastapi==0.104.1)
- [ ] Add Uvicorn dependency (uvicorn[standard]==0.24.0)
- [ ] Add SQLAlchemy dependency (sqlalchemy==2.0.23)
- [ ] Add Alembic dependency (alembic==1.12.1)
- [ ] Add PostgreSQL driver (psycopg2-binary==2.9.9)
- [ ] Add Celery dependency (celery==5.3.4)
- [ ] Add Redis dependency (redis==5.0.1)
- [ ] Add SendGrid dependency (sendgrid==6.11.0)
- [ ] Add environment/config dependencies (python-dotenv==1.0.0, pydantic==2.5.0, pydantic-settings==2.1.0)
- [ ] Add utility dependencies (python-dateutil==2.8.2, pytz==2023.3)
- [ ] Add development dependencies (pytest==7.4.3, pytest-asyncio==0.21.1, black==23.11.0, flake8==6.1.0, mypy==1.7.0)
- [ ] Install all dependencies (`pip install -r requirements.txt`)
- [ ] Verify all packages installed successfully
- [ ] Test imports (try importing fastapi, sqlalchemy, celery, etc.)

#### 2.4 Backend Environment Variables
- [ ] Create `backend/.env.example` file
- [ ] Add DATABASE_URL with placeholder
- [ ] Add REDIS_URL with placeholder
- [ ] Add API_HOST, API_PORT, API_RELOAD settings
- [ ] Add CELERY_BROKER_URL and CELERY_RESULT_BACKEND
- [ ] Add EMAIL_SERVICE setting
- [ ] Add SENDGRID_API_KEY placeholder
- [ ] Add ADMIN_EMAIL placeholder
- [ ] Add SECRET_KEY and API_KEY placeholders
- [ ] Add ENVIRONMENT setting
- [ ] Create `backend/.env` file (copy from .env.example)
- [ ] Document which values need to be filled in
- [ ] Verify .env is in .gitignore

#### 2.5 Backend Configuration Files
- [ ] Create `backend/app/main.py` placeholder file
- [ ] Add basic FastAPI app structure (will be implemented in Backend Services phase)
- [ ] Create basic CORS configuration structure
- [ ] Document structure for future implementation

---

### 3. Database Services Setup

#### 3.1 PostgreSQL Setup
- [ ] Verify PostgreSQL 14+ is installed OR document Docker alternative
- [ ] Create local database (`createdb tutor_scoring` or equivalent)
- [ ] Test database connection
- [ ] Update DATABASE_URL in backend/.env
- [ ] Document Docker setup option (`docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=password postgres:15`)
- [ ] Verify connection string format is correct

#### 3.2 Redis Setup
- [ ] Verify Redis 7+ is installed OR document Docker alternative
- [ ] Test Redis connection
- [ ] Update REDIS_URL in backend/.env
- [ ] Document Docker setup option (`docker run -d -p 6379:6379 redis:7`)
- [ ] Verify connection string format is correct
- [ ] Test Redis with basic commands

---

### 4. Frontend Environment Setup

#### 4.1 Node.js Environment
- [ ] Verify Node.js 18+ (LTS) is installed
- [ ] Verify npm or yarn is available
- [ ] Test Node.js version compatibility

#### 4.2 Frontend Directory Structure
- [ ] Create `frontend/src/` directory
- [ ] Create `frontend/src/components/` directory
- [ ] Create `frontend/src/pages/` directory
- [ ] Create `frontend/src/services/` directory
- [ ] Create `frontend/src/hooks/` directory
- [ ] Create `frontend/src/utils/` directory
- [ ] Create `frontend/public/` directory
- [ ] Verify structure matches PRD specification

#### 4.3 Frontend Dependencies
- [ ] Create `frontend/package.json` file
- [ ] Add React dependencies (react, react-dom)
- [ ] Add React Router (react-router-dom)
- [ ] Add HTTP client (axios)
- [ ] Add charting library (recharts)
- [ ] Add state management (@tanstack/react-query)
- [ ] Add development dependencies (vite, @vitejs/plugin-react, eslint, prettier)
- [ ] Install all dependencies (`npm install`)
- [ ] Verify all packages installed successfully
- [ ] Test that React can be imported

#### 4.4 Frontend Configuration
- [ ] Create `frontend/vite.config.js` file
- [ ] Configure Vite with React plugin
- [ ] Set up server configuration (port 3000)
- [ ] Configure proxy for API calls (/api -> http://localhost:8000)
- [ ] Configure build settings (outDir: 'dist', sourcemap: true)
- [ ] Test Vite configuration

#### 4.5 Frontend Environment Variables
- [ ] Create `frontend/.env.example` file
- [ ] Add VITE_API_URL placeholder
- [ ] Add VITE_API_KEY placeholder
- [ ] Create `frontend/.env` file (copy from .env.example)
- [ ] Set VITE_API_URL to http://localhost:8000
- [ ] Verify .env is in .gitignore

#### 4.6 Frontend Entry Point
- [ ] Create `frontend/src/App.jsx` placeholder file
- [ ] Create `frontend/src/main.jsx` entry point
- [ ] Add basic React app structure (will be implemented in Frontend Dashboard phase)
- [ ] Document structure for future implementation

---

### 5. Development Tools Setup

#### 5.1 Code Quality Tools (Backend)
- [ ] Verify Black formatter is installed
- [ ] Test Black formatting (`black --check .`)
- [ ] Verify Flake8 linter is installed
- [ ] Test Flake8 linting (`flake8 .`)
- [ ] Verify MyPy type checker is installed
- [ ] Create basic mypy.ini configuration (optional)
- [ ] Document usage of each tool

#### 5.2 Pre-commit Hooks (Optional)
- [ ] Install pre-commit (`pip install pre-commit`)
- [ ] Create `.pre-commit-config.yaml` file
- [ ] Configure Black hook
- [ ] Configure Flake8 hook
- [ ] Run `pre-commit install`
- [ ] Test pre-commit hooks

---

### 6. Deployment Configuration

#### 6.1 Render Configuration Files
- [ ] Create `render.yaml` file in project root
- [ ] Configure backend web service:
  - Set type: web
  - Set name: tutor-scoring-api
  - Set build command: `pip install -r requirements.txt`
  - Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
  - Configure environment variables (DATABASE_URL, REDIS_URL, etc.)
- [ ] Configure background worker service:
  - Set type: worker
  - Set name: tutor-scoring-worker
  - Set build command: `pip install -r requirements.txt`
  - Set start command: `celery -A app.tasks.celery_app worker --loglevel=info`
  - Configure environment variables
- [ ] Configure frontend static site:
  - Set build command: `cd frontend && npm install && npm run build`
  - Set publish directory: `frontend/dist`
  - Configure environment variables
- [ ] Verify render.yaml syntax is correct
- [ ] Document Render service setup requirements

#### 6.2 Docker Configuration (Optional)
- [ ] Create `docker-compose.yml` file (optional, for local development)
- [ ] Configure PostgreSQL service
- [ ] Configure Redis service
- [ ] Document Docker usage for local development
- [ ] Test docker-compose setup (optional)

---

### 7. Database Migration Setup

#### 7.1 Alembic Initialization
- [ ] Navigate to backend directory
- [ ] Initialize Alembic (`alembic init alembic`)
- [ ] Verify alembic/ directory structure created
- [ ] Configure `alembic/env.py` to use DATABASE_URL from environment
- [ ] Configure `alembic.ini` with database connection
- [ ] Test Alembic connection
- [ ] Document migration workflow

---

### 8. Documentation

#### 8.1 README.md
- [ ] Create root `README.md` file
- [ ] Add project overview section
- [ ] Add quick start guide
- [ ] Add setup instructions for backend
- [ ] Add setup instructions for frontend
- [ ] Add database setup instructions
- [ ] Add Redis setup instructions
- [ ] Add development workflow section
- [ ] Add API documentation link (FastAPI auto-generates)
- [ ] Add deployment instructions
- [ ] Add troubleshooting section
- [ ] Add contributing guidelines (if applicable)

#### 8.2 Development Documentation
- [ ] Document environment variable requirements
- [ ] Document database connection setup
- [ ] Document Redis connection setup
- [ ] Document local development startup process
- [ ] Document testing setup
- [ ] Document code quality tools usage

---

### 9. Verification & Testing

#### 9.1 Backend Verification
- [ ] Activate Python virtual environment
- [ ] Verify all imports work (fastapi, sqlalchemy, celery, etc.)
- [ ] Test FastAPI can start (even if basic app)
- [ ] Test database connection works
- [ ] Test Redis connection works
- [ ] Verify Celery can be imported
- [ ] Run Black formatter (should complete without errors)
- [ ] Run Flake8 linter (may have warnings, but no critical errors)

#### 9.2 Frontend Verification
- [ ] Navigate to frontend directory
- [ ] Verify all dependencies installed
- [ ] Test Vite dev server can start (`npm run dev`)
- [ ] Verify React app loads (even if basic)
- [ ] Test API proxy configuration
- [ ] Verify build works (`npm run build`)

#### 9.3 Database Verification
- [ ] Test PostgreSQL connection
- [ ] Verify database exists and is accessible
- [ ] Test basic SQL queries work
- [ ] Verify Alembic can connect

#### 9.4 Redis Verification
- [ ] Test Redis connection
- [ ] Verify Redis is running
- [ ] Test basic Redis commands (SET, GET)
- [ ] Verify Celery broker can connect to Redis

#### 9.5 Integration Verification
- [ ] Verify backend can start without errors
- [ ] Verify Celery worker can start (even if no tasks yet)
- [ ] Verify frontend can start without errors
- [ ] Verify frontend can make API calls (when backend is running)
- [ ] Test end-to-end: backend running, frontend running, can communicate

---

### 10. Final Checklist

#### 10.1 Project Structure
- [ ] All directories created according to PRD
- [ ] All placeholder files created
- [ ] Directory structure matches specification exactly

#### 10.2 Dependencies
- [ ] All backend dependencies installed
- [ ] All frontend dependencies installed
- [ ] No version conflicts
- [ ] All imports work correctly

#### 10.3 Configuration
- [ ] Environment variables configured
- [ ] .env files created and working
- [ ] .env.example files created and documented
- [ ] All .env files in .gitignore

#### 10.4 Services
- [ ] PostgreSQL running and accessible
- [ ] Redis running and accessible
- [ ] Connection strings correct in .env files
- [ ] Services can be started/stopped easily

#### 10.5 Deployment Ready
- [ ] render.yaml configured correctly
- [ ] All environment variables documented
- [ ] Build commands tested locally
- [ ] Start commands verified

#### 10.6 Documentation
- [ ] README.md complete and helpful
- [ ] Setup instructions clear
- [ ] Troubleshooting section added
- [ ] Development workflow documented

#### 10.7 Git
- [ ] Repository initialized
- [ ] .gitignore configured correctly
- [ ] No sensitive files committed
- [ ] Initial commit ready (optional)

---

## Success Criteria

All tasks must be completed and verified before proceeding to Data Foundation phase:

- ✅ Python environment set up and working
- ✅ All backend dependencies installed
- ✅ PostgreSQL database created and accessible
- ✅ Redis running and accessible
- ✅ Backend can start without errors
- ✅ Celery worker can start (basic structure)
- ✅ Node.js environment set up
- ✅ All frontend dependencies installed
- ✅ Frontend can start without errors
- ✅ Environment variables configured
- ✅ Git repository initialized
- ✅ .gitignore configured correctly
- ✅ README.md created with comprehensive instructions
- ✅ Render configuration files created
- ✅ Project structure matches PRD specification
- ✅ All services (PostgreSQL, Redis) verified working
- ✅ Development tools (Black, Flake8) working

---

## Dependencies

### Required Software (Must be installed)
- Python 3.11+
- Node.js 18+ (LTS)
- PostgreSQL 14+ (or Docker)
- Redis 7+ (or Docker)
- Git

### Required Accounts (For deployment)
- GitHub account (for repository)
- Render account (for deployment)
- SendGrid account (for email service) or AWS account (for SES)

### Optional Tools
- Docker (for local containerized development)
- VS Code or preferred IDE
- Postman or similar (for API testing)

---

## Next Steps

After completing Environment Setup:

1. **Data Foundation & Models** (Next Phase)
   - Database schema design
   - SQLAlchemy models
   - Database migrations
   - Synthetic data generator

2. **Backend Services** (Following Phase)
   - FastAPI application implementation
   - API endpoints
   - Celery tasks
   - Email service

3. **Frontend Dashboard** (Final Phase)
   - React application implementation
   - Dashboard components
   - API integration
   - Visualizations

---

## Notes

- This is a foundation phase - all subsequent development depends on this
- Take time to verify each step works before moving to the next
- Document any deviations from the PRD
- Keep environment variables secure and never commit them
- Test both local and Render deployment configurations
- If using Docker, ensure docker-compose.yml is well-documented

---

## Troubleshooting

### Common Issues

**Backend:**
- Import errors: Check virtual environment is activated
- Database connection: Verify PostgreSQL is running and DATABASE_URL is correct
- Redis connection: Verify Redis is running and REDIS_URL is correct

**Frontend:**
- Module not found: Run `npm install`
- API connection: Check VITE_API_URL matches backend URL
- CORS errors: Will be configured in Backend Services phase

**Database:**
- Connection refused: Check PostgreSQL is running
- Authentication failed: Verify username/password in DATABASE_URL
- Database not found: Create database first

**Redis:**
- Connection refused: Check Redis is running
- Cannot connect: Verify REDIS_URL is correct format

---

**Last Updated:** [Date]  
**Status:** Not Started  
**Assigned To:** [Developer Name]

