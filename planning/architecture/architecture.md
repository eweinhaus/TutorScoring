# System Architecture

## Architecture Diagram

See `architecture.mmd` for the mermaid diagram.

## Component Descriptions

### Frontend Layer
- **React Dashboard**: Real-time visualization of tutor performance, risk flags, and insights
- Serves static assets, connects to API for data

### API Layer
- **FastAPI Backend**: RESTful API handling session ingestion, tutor queries, dashboard data
- **Authentication**: Middleware for API security (JWT tokens)

### Data Processing Layer
- **Background Job Queue**: Celery workers processing sessions asynchronously
- **Session Processor**: Orchestrates scoring and analysis for each session
- **Reschedule Analyzer**: Calculates reschedule rates and flags high-risk tutors

### AI Services
- **OpenAI API**: Used for advanced analysis (first session quality, pattern detection in future phases)

### Data Layer
- **PostgreSQL**: Primary database for sessions, tutors, scores, and historical data
- **Redis**: Job queue broker and caching layer

### External Services
- **Email Service**: Sends automated per-session reports to admins
- **Rails Application**: Existing platform integration (mock for MVP, real for production)

### Data Generation
- **Synthetic Data Generator**: Python script to create realistic session and tutor data for demo

## Data Flow

### Session Processing Flow
1. Session completed in Rails app → Webhook/API call to FastAPI
2. FastAPI receives session data → Creates job in queue
3. Background worker picks up job → Processes session
4. Processor calculates reschedule risk (if applicable)
5. Processor updates tutor scores in database
6. Processor generates email report → Sends to admin
7. Dashboard polls API → Updates UI with new data

### Dashboard Query Flow
1. User opens dashboard → React app loads
2. React calls API endpoints → Gets tutor list, scores, flags
3. API queries PostgreSQL → Returns aggregated data
4. Dashboard renders visualizations and insights

## Technology Stack

### Backend
- **FastAPI** (Python): Modern, fast API framework
- **Celery**: Distributed task queue
- **PostgreSQL**: Relational database
- **Redis**: Message broker and cache

### Frontend
- **React**: UI framework
- **Recharts/Chart.js**: Data visualization
- **Axios**: HTTP client

### AI/ML
- **OpenAI API**: GPT-4 for text analysis
- **Python**: Data processing and analysis

### Infrastructure (MVP)
- **Render**: Backend services (API, Workers, Database)
- **Static Hosting**: Dashboard frontend

### Infrastructure (Production)
- **AWS**: EC2/ECS for compute, RDS for database, S3 for storage
- **Lambda**: Serverless processing for scale

## Scalability Considerations

### MVP (Render)
- Single worker instance processing jobs sequentially
- PostgreSQL database with basic indexing
- Suitable for ~3,000 sessions/day with 1-hour processing window

### Production (AWS)
- Multiple Celery workers (horizontal scaling)
- RDS with read replicas for dashboard queries
- SQS for job queue (instead of Redis)
- CloudWatch for monitoring and alerting
- Auto-scaling based on queue depth

