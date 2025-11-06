# Tutor Quality Scoring System - MVP

## 🌐 Live Application

**Deployed Application:** [https://d2iu6aqgs7qt5d.cloudfront.net](https://d2iu6aqgs7qt5d.cloudfront.net)

- **Frontend:** https://d2iu6aqgs7qt5d.cloudfront.net
- **API Endpoint:** https://d2iu6aqgs7qt5d.cloudfront.net/api/*
- **API Health Check:** https://d2iu6aqgs7qt5d.cloudfront.net/api/health
- **Infrastructure:** AWS (CloudFront, S3, ALB, RDS, ElastiCache)

**Note:** If you see cached content, perform a hard refresh:
- **Mac:** `Cmd + Shift + R`
- **Windows/Linux:** `Ctrl + Shift + R`

---

Automated system that evaluates tutor performance, identifies retention risks, and provides actionable insights to reduce churn. The MVP focuses on detecting high reschedule rates with a clean dashboard interface and automated reporting.

## 🎯 Project Overview

This system processes 3,000 daily sessions, calculates tutor reschedule rates, and flags at-risk tutors with >15% reschedule rate. It provides a React dashboard for administrators and automated email reports per session.

**Tech Stack:**
- **Backend:** FastAPI (Python 3.11+), Celery, PostgreSQL, Redis
- **Frontend:** React, Vite, Recharts
- **Infrastructure:** Render (MVP), AWS-ready architecture

## 📋 Prerequisites

### Required Software
- **Python 3.11+** (verify with `python3 --version`)
- **Node.js 18+ LTS** (verify with `node --version`)
- **PostgreSQL 14+** (or Docker)
- **Redis 7+** (or Docker)
- **Git**

### Required Accounts (For Deployment)
- GitHub account (for repository)
- Render account (for deployment)
- SendGrid account (for email service) or AWS account (for SES)

### Optional Tools
- Docker (for local containerized development)
- VS Code or preferred IDE
- Postman or similar (for API testing)

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone <repository-url>
cd TutorScoring
```

### 2. Backend Setup

#### Create Virtual Environment
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Configure Environment Variables
```bash
cp .env.example .env
# Edit .env and update the following:
# - DATABASE_URL: PostgreSQL connection string
# - REDIS_URL: Redis connection string
# - SENDGRID_API_KEY: Your SendGrid API key
# - SECRET_KEY: Generate a secure secret key
# - API_KEY: Generate an API key
```

#### Start Backend Server
```bash
uvicorn app.main:app --reload
```
The API will be available at `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/api/health`

### 3. Frontend Setup

#### Install Dependencies
```bash
cd frontend
npm install
```

#### Configure Environment Variables
```bash
cp .env.example .env
# Edit .env and set:
# VITE_API_URL=http://localhost:8000
# VITE_API_KEY=your-api-key-here
```

#### Start Development Server
```bash
npm run dev
```
The frontend will be available at `http://localhost:3000`

### 4. Database Setup

#### PostgreSQL (Local)
```bash
# Create database
createdb tutor_scoring

# Or using psql
psql -U postgres
CREATE DATABASE tutor_scoring;
```

#### PostgreSQL (Docker)
```bash
docker run -d \
  --name tutor-scoring-postgres \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=tutor_scoring \
  postgres:15
```

#### Redis (Local)
```bash
# Install Redis (macOS)
brew install redis
redis-server

# Or using Docker
docker run -d \
  --name tutor-scoring-redis \
  -p 6379:6379 \
  redis:7
```

### 5. Database Migrations

```bash
cd backend
source venv/bin/activate

# Initialize Alembic (already done)
# alembic init alembic

# Create migration (when models are ready)
# alembic revision --autogenerate -m "Initial schema"

# Apply migrations
# alembic upgrade head
```

## 🏗️ Project Structure

```
TutorScoring/
├── backend/                 # FastAPI backend application
│   ├── app/
│   │   ├── api/            # API route handlers
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   ├── tasks/           # Celery tasks
│   │   ├── utils/           # Utility functions
│   │   ├── middleware/    # Middleware components
│   │   └── main.py          # FastAPI application entry point
│   ├── alembic/             # Database migrations
│   ├── tests/               # Backend tests
│   ├── requirements.txt     # Python dependencies
│   └── .env.example         # Environment variables template
│
├── frontend/                # React frontend application
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/           # Page components
│   │   ├── services/        # API client services
│   │   ├── hooks/           # Custom React hooks
│   │   ├── utils/           # Utility functions
│   │   └── App.jsx          # Main app component
│   ├── public/              # Static assets
│   ├── package.json         # Node dependencies
│   └── vite.config.js       # Vite configuration
│
├── scripts/                 # Utility scripts
├── planning/                # Project documentation
│   ├── PRD_MVP.md          # Main product requirements
│   ├── PRDs/               # Sub-PRDs
│   └── tasks/              # Task lists
│
├── render.yaml              # Render deployment configuration
└── README.md               # This file
```

## 🔧 Development Workflow

### Backend Development
```bash
cd backend
source venv/bin/activate

# Start development server with auto-reload
uvicorn app.main:app --reload

# Run Celery worker (in separate terminal)
celery -A app.tasks.celery_app worker --loglevel=info

# Run tests
pytest

# Format code
black .

# Lint code
flake8 .
```

### Frontend Development
```bash
cd frontend

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

### Code Quality Tools

#### Backend
- **Black**: Code formatter (`black .`)
- **Flake8**: Linter (`flake8 .`)
- **MyPy**: Type checking (`mypy .`)

#### Frontend
- **ESLint**: JavaScript linter
- **Prettier**: Code formatter

## 📦 Deployment

### Render Deployment

The project includes a `render.yaml` configuration file for easy deployment to Render.

#### Services to Create on Render:
1. **PostgreSQL Database**
   - Name: `tutor-scoring-db`
   - Render will automatically provide connection string

2. **Redis Instance**
   - Name: `tutor-scoring-redis`
   - Render will automatically provide connection string

3. **Backend API** (Web Service)
   - Connected to PostgreSQL and Redis
   - Environment variables configured in `render.yaml`

4. **Background Worker** (Worker Service)
   - Connected to PostgreSQL and Redis
   - Runs Celery workers

5. **Frontend** (Static Site)
   - Builds from `frontend/` directory
   - Serves from `frontend/dist`

#### Deployment Steps:
1. Push code to GitHub
2. Connect repository to Render
3. Render will detect `render.yaml` and create services
4. Set additional environment variables in Render dashboard:
   - `SENDGRID_API_KEY`
   - `ADMIN_EMAIL`
   - `SECRET_KEY`
   - `API_KEY`
5. Run database migrations:
   ```bash
   cd backend
   alembic upgrade head
   ```

## 🧪 Testing

### Backend Tests
```bash
cd backend
source venv/bin/activate
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

### Integration Tests
- Test API endpoints with Postman or curl
- Verify frontend can connect to backend
- Test Celery task processing

## 🐛 Troubleshooting

### Backend Issues

**Import errors:**
- Ensure virtual environment is activated: `source venv/bin/activate`
- Verify all dependencies are installed: `pip install -r requirements.txt`

**Database connection errors:**
- Verify PostgreSQL is running: `pg_isready` or `psql -U postgres`
- Check `DATABASE_URL` in `.env` is correct format
- Ensure database exists: `createdb tutor_scoring`

**Redis connection errors:**
- Verify Redis is running: `redis-cli ping`
- Check `REDIS_URL` in `.env` is correct
- Test connection: `redis-cli -u $REDIS_URL ping`

**FastAPI won't start:**
- Check for syntax errors in `main.py`
- Verify all imports are available
- Check port 8000 is not in use

### Frontend Issues

**Module not found:**
- Run `npm install` to install dependencies
- Delete `node_modules` and `package-lock.json`, then reinstall

**API connection errors:**
- Verify `VITE_API_URL` in `.env` matches backend URL
- Check backend is running on port 8000
- Verify CORS is configured in FastAPI

**Build errors:**
- Check Node.js version: `node --version` (should be 18+)
- Clear cache: `rm -rf node_modules .vite`
- Reinstall: `npm install`

### Database Issues

**Connection refused:**
- Check PostgreSQL is running
- Verify port 5432 is not blocked
- Check firewall settings

**Authentication failed:**
- Verify username/password in `DATABASE_URL`
- Check PostgreSQL user permissions

**Database not found:**
- Create database: `createdb tutor_scoring`
- Or use Docker container

### Redis Issues

**Connection refused:**
- Check Redis is running: `redis-cli ping`
- Verify port 6379 is not blocked

**Cannot connect:**
- Verify `REDIS_URL` format: `redis://localhost:6379/0`
- Check Redis is not password-protected locally

## 📚 Documentation

### Project Documentation
- **Main PRD:** `planning/PRD_MVP.md`
- **Sub-PRDs:** `planning/PRDs/`
  - `PRD_Environment_Setup.md`
  - `PRD_Data_Foundation.md`
  - `PRD_Backend_Services.md`
  - `PRD_Frontend_Dashboard.md`
- **Architecture:** `planning/architecture/`
- **Task Lists:** `planning/tasks/`

### API Documentation
- FastAPI automatically generates interactive docs at `/docs` when server is running
- OpenAPI schema available at `/openapi.json`

## 🔐 Security Notes

- Never commit `.env` files to Git
- Use strong `SECRET_KEY` and `API_KEY` values in production
- Rotate API keys regularly
- Use environment variables for all sensitive configuration
- Keep dependencies updated for security patches

## 📝 Environment Variables

### Backend (.env)
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `CELERY_BROKER_URL`: Celery broker URL
- `CELERY_RESULT_BACKEND`: Celery result backend URL
- `EMAIL_SERVICE`: Email service provider (sendgrid/ses)
- `SENDGRID_API_KEY`: SendGrid API key
- `ADMIN_EMAIL`: Admin email for reports
- `SECRET_KEY`: Secret key for encryption
- `API_KEY`: API key for authentication
- `ENVIRONMENT`: Environment (development/production)

### Frontend (.env)
- `VITE_API_URL`: Backend API URL
- `VITE_API_KEY`: API key for requests

## 🎯 Success Criteria

Before proceeding to next phase, verify:
- ✅ Python environment set up and working
- ✅ All backend dependencies installed
- ✅ PostgreSQL database created and accessible
- ✅ Redis running and accessible
- ✅ Backend can start without errors
- ✅ Celery worker can start
- ✅ Node.js environment set up
- ✅ All frontend dependencies installed
- ✅ Frontend can start without errors
- ✅ Environment variables configured
- ✅ Git repository initialized
- ✅ .gitignore configured correctly
- ✅ Render configuration files created

## 🚦 Next Steps

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

## 📄 License

[Add license information here]

## 👥 Contributors

[Add contributor information here]

---

**Status:** Environment Setup Phase  
**Last Updated:** [Date]  
**Version:** 1.0.0

