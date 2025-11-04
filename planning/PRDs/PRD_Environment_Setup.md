# Sub-PRD: Environment Setup
## Tutor Quality Scoring System - MVP

**Version:** 1.0  
**Parent PRD:** PRD_MVP.md  
**Status:** Ready for Implementation

---

## 1. Overview

### 1.1 Purpose
Establish the foundational development environment, project structure, and tooling required for the Tutor Quality Scoring System MVP. This phase sets up the complete development workflow before building any application code.

### 1.2 Goals
- Create clean, organized project structure
- Set up local development environment
- Configure development tools and dependencies
- Establish deployment-ready configuration
- Enable team collaboration with consistent setup

### 1.3 Success Criteria
- ✅ All developers can run the project locally with minimal setup
- ✅ Project structure is clear and maintainable
- ✅ Dependencies are documented and managed
- ✅ Development tools are configured and working
- ✅ Ready for Render deployment configuration

---

## 2. Project Structure

### 2.1 Directory Layout

```
TutorScoring/
├── backend/                 # FastAPI backend application
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py         # FastAPI application entry point
│   │   ├── api/            # API route handlers
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   ├── tasks/          # Celery tasks
│   │   └── utils/          # Utility functions
│   ├── alembic/            # Database migrations
│   ├── tests/              # Backend tests
│   ├── requirements.txt    # Python dependencies
│   ├── .env.example        # Environment variables template
│   └── Dockerfile          # Container configuration (optional)
│
├── frontend/               # React frontend application
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API client services
│   │   ├── hooks/          # Custom React hooks
│   │   ├── utils/          # Utility functions
│   │   └── App.jsx         # Main app component
│   ├── public/             # Static assets
│   ├── package.json        # Node dependencies
│   ├── .env.example        # Environment variables template
│   └── vite.config.js      # Vite configuration
│
├── scripts/                # Utility scripts
│   ├── generate_data.py    # Synthetic data generator
│   └── setup_db.py         # Database initialization
│
├── planning/               # Project documentation
│   ├── PRD_MVP.md
│   ├── PRD_*.md           # Sub-PRDs
│   ├── architecture.md
│   └── roadmap.md
│
├── .gitignore              # Git ignore rules
├── README.md               # Project overview
└── docker-compose.yml      # Local development containers (optional)
```

### 2.2 File Organization Principles
- **Separation of Concerns**: Backend and frontend in separate directories
- **Modularity**: Clear separation of API routes, models, services, tasks
- **Scalability**: Structure supports future growth
- **Convention**: Follow framework conventions (FastAPI, React)

---

## 3. Backend Environment Setup

### 3.1 Python Environment

**Requirements:**
- Python 3.11+ (recommended: 3.11 or 3.12)
- Virtual environment management (venv or poetry)

**Setup Steps:**
1. Create virtual environment: `python -m venv venv` or `poetry install`
2. Activate environment: `source venv/bin/activate` (Mac/Linux) or `venv\Scripts\activate` (Windows)
3. Install dependencies: `pip install -r requirements.txt`

**Dependencies (requirements.txt):**
```
# Web Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0

# Database
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.9

# Task Queue
celery==5.3.4
redis==5.0.1

# Email
sendgrid==6.11.0
# OR
# boto3==1.29.7  # For AWS SES

# Environment & Config
python-dotenv==1.0.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Utilities
python-dateutil==2.8.2
pytz==2023.3

# Development
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.11.0
flake8==6.1.0
mypy==1.7.0
```

### 3.2 Environment Variables

Create `.env` file (use `.env.example` as template):

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/tutor_scoring

# Redis
REDIS_URL=redis://localhost:6379/0

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true  # For development

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Email Service
EMAIL_SERVICE=sendgrid  # or 'ses'
SENDGRID_API_KEY=your_sendgrid_key
# OR for SES
# AWS_ACCESS_KEY_ID=your_key
# AWS_SECRET_ACCESS_KEY=your_secret
# AWS_REGION=us-east-1

# Admin Email
ADMIN_EMAIL=admin@example.com

# Security
SECRET_KEY=your-secret-key-here
API_KEY=your-api-key-here

# Environment
ENVIRONMENT=development  # development, staging, production
```

### 3.3 Database Setup

**Local PostgreSQL:**
- Install PostgreSQL 14+ locally
- Create database: `createdb tutor_scoring`
- Or use Docker: `docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=password postgres:15`

**Connection:**
- Default connection string: `postgresql://postgres:password@localhost:5432/tutor_scoring`
- Update `DATABASE_URL` in `.env`

### 3.4 Redis Setup

**Local Redis:**
- Install Redis 7+ locally
- Or use Docker: `docker run -d -p 6379:6379 redis:7`

**Connection:**
- Default connection: `redis://localhost:6379/0`
- Update `REDIS_URL` in `.env`

### 3.5 Development Tools

**Code Quality:**
- **Black**: Code formatter (`black .`)
- **Flake8**: Linter (`flake8 .`)
- **MyPy**: Type checking (`mypy .`)

**Pre-commit Hooks (Optional):**
- Install pre-commit: `pip install pre-commit`
- Create `.pre-commit-config.yaml`
- Run: `pre-commit install`

---

## 4. Frontend Environment Setup

### 4.1 Node.js Environment

**Requirements:**
- Node.js 18+ (LTS recommended)
- npm or yarn package manager

**Setup Steps:**
1. Navigate to frontend: `cd frontend`
2. Install dependencies: `npm install`
3. Start development server: `npm run dev`

**Dependencies (package.json):**
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "axios": "^1.6.2",
    "recharts": "^2.10.3",
    "@tanstack/react-query": "^5.8.4"
  },
  "devDependencies": {
    "vite": "^5.0.0",
    "@vitejs/plugin-react": "^4.2.0",
    "eslint": "^8.54.0",
    "prettier": "^3.1.0"
  }
}
```

### 4.2 Environment Variables

Create `frontend/.env` file:

```bash
VITE_API_URL=http://localhost:8000
VITE_API_KEY=your-api-key-here
```

### 4.3 Build Configuration

**Vite Configuration (vite.config.js):**
```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  }
})
```

---

## 5. Development Workflow

### 5.1 Local Development Startup

**Backend:**
```bash
cd backend
source venv/bin/activate  # or poetry shell
python -m uvicorn app.main:app --reload
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

### 5.2 Database Migrations

**Initialize Alembic:**
```bash
cd backend
alembic init alembic
```

**Create Migration:**
```bash
alembic revision --autogenerate -m "Initial schema"
```

**Apply Migration:**
```bash
alembic upgrade head
```

### 5.3 Testing Setup

**Backend Tests:**
- Create `backend/tests/` directory
- Use pytest for testing
- Run: `pytest backend/tests/`

**Frontend Tests:**
- Optional: Add Vitest or Jest
- Run: `npm test`

---

## 6. Render Deployment Configuration

### 6.1 Backend Service (Render)

**render.yaml:**
```yaml
services:
  - type: web
    name: tutor-scoring-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: tutor-scoring-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          name: tutor-scoring-redis
          type: redis
          property: connectionString
      - key: ENVIRONMENT
        value: production
```

**Environment Variables on Render:**
- Set via Render dashboard
- Use Render's environment variable management
- Connect to Render PostgreSQL and Redis services

### 6.2 Background Worker (Render)

**render.yaml:**
```yaml
services:
  - type: worker
    name: tutor-scoring-worker
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: celery -A app.tasks.celery_app worker --loglevel=info
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: tutor-scoring-db
          property: connectionString
      - key: CELERY_BROKER_URL
        fromService:
          name: tutor-scoring-redis
          type: redis
          property: connectionString
```

### 6.3 Database (Render PostgreSQL)

- Create PostgreSQL database on Render
- Name: `tutor-scoring-db`
- Connection string automatically provided

### 6.4 Redis (Render Redis)

- Create Redis instance on Render
- Name: `tutor-scoring-redis`
- Connection string automatically provided

### 6.5 Frontend (Render Static Site)

- Connect GitHub repository
- Build command: `cd frontend && npm install && npm run build`
- Publish directory: `frontend/dist`
- Environment variables: Set `VITE_API_URL` to backend URL

---

## 7. Git Configuration

### 7.1 .gitignore

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
.venv
*.egg-info/
dist/
build/

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
dist/
build/

# Environment
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Database
*.db
*.sqlite

# Logs
*.log
logs/

# OS
.DS_Store
Thumbs.db
```

### 7.2 Git Workflow

- Main branch: `main`
- Feature branches: `feature/description`
- Commit messages: Conventional commits format
- PR reviews before merging

---

## 8. Documentation

### 8.1 README.md

Include:
- Project overview
- Quick start guide
- Setup instructions
- Development workflow
- API documentation links
- Deployment instructions

### 8.2 Development Documentation

- API endpoint documentation (FastAPI auto-generates)
- Database schema documentation
- Environment variable documentation
- Troubleshooting guide

---

## 9. Verification Checklist

Before proceeding to next phase, verify:

- [ ] Python environment set up and working
- [ ] All backend dependencies installed
- [ ] PostgreSQL database created and accessible
- [ ] Redis running and accessible
- [ ] Backend can start without errors
- [ ] Celery worker can start
- [ ] Node.js environment set up
- [ ] All frontend dependencies installed
- [ ] Frontend can start without errors
- [ ] Environment variables configured
- [ ] Git repository initialized
- [ ] .gitignore configured
- [ ] README.md created
- [ ] Render configuration files created
- [ ] Project structure matches specification

---

## 10. Next Steps

After completing environment setup:

1. **Data Foundation & Models** (Next Sub-PRD)
   - Database schema design
   - SQLAlchemy models
   - Database migrations
   - Synthetic data generator

2. **Backend Services** (Following Sub-PRD)
   - FastAPI application
   - API endpoints
   - Celery tasks
   - Email service

3. **Frontend Dashboard** (Final Sub-PRD)
   - React application
   - Dashboard components
   - API integration

---

## 11. Troubleshooting

### Common Issues

**Backend:**
- Import errors: Check virtual environment is activated
- Database connection: Verify PostgreSQL is running and DATABASE_URL is correct
- Redis connection: Verify Redis is running and REDIS_URL is correct

**Frontend:**
- Module not found: Run `npm install`
- API connection: Check VITE_API_URL matches backend URL
- CORS errors: Configure CORS in FastAPI

**Deployment:**
- Build failures: Check build logs on Render
- Environment variables: Verify all required vars are set
- Database migrations: Run migrations on Render database

---

## 12. Dependencies & Prerequisites

### Required Software
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis 7+
- Git

### Required Accounts
- GitHub account (for repository)
- Render account (for deployment)
- SendGrid account (for email service) or AWS account (for SES)

### Optional Tools
- Docker (for local containerized development)
- VS Code or preferred IDE
- Postman or similar (for API testing)

