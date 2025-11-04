# Product Requirements Document (PRD)
## Tutor Quality Scoring System - MVP

**Version:** 1.0  
**Date:** 2024  
**Status:** MVP Phase

---

## 1. Executive Summary

### 1.1 Purpose
Build an automated system that evaluates tutor performance, identifies retention risks, and provides actionable insights to reduce churn. The MVP focuses on detecting high reschedule rates with a clean dashboard interface and automated reporting.

### 1.2 Goals
- Flag tutors with high rescheduling rates (MVP focus)
- Provide real-time dashboard for tutor performance monitoring
- Generate automated email reports per session for administrators
- Demonstrate AI-powered insights capability (foundation for future features)
- Show clear path to production deployment

### 1.3 Success Criteria
- **Functional**: System processes sessions, calculates reschedule rates, displays on dashboard
- **Performance**: Handles 3,000 daily sessions with 1-hour processing latency
- **User Experience**: Clean, intuitive dashboard that clearly shows risk flags
- **Business Value**: Identifies at-risk tutors with actionable recommendations
- **Demo Ready**: Can showcase working system in 5-minute demo video

---

## 2. Problem Statement

### 2.1 Business Problem
- 24% of churners have poor first session experiences
- 98.2% of reschedules are tutor-initiated, indicating reliability issues
- 16% of tutor replacements are due to no-shows
- No automated system exists to identify at-risk tutors proactively

### 2.2 Current State
- Manual monitoring of tutor performance
- Reactive approach to tutor issues
- No predictive insights for retention
- Limited visibility into patterns across 3,000 daily sessions

### 2.3 Desired State
- Automated scoring and flagging of at-risk tutors
- Proactive identification of retention risks
- Actionable insights delivered to administrators
- Data-driven coaching recommendations

---

## 3. MVP Scope

### 3.1 In Scope

#### Core Features
1. **Reschedule Rate Flagging**
   - Calculate reschedule rate per tutor (tutor-initiated reschedules / total sessions)
   - Flag tutors exceeding threshold (e.g., >15% reschedule rate)
   - Track reschedule frequency over time windows (7-day, 30-day, 90-day)

2. **Dashboard Interface**
   - Tutor list view with reschedule rate flags
   - Individual tutor detail view
   - Reschedule rate trends over time
   - Risk score visualization
   - Filtering and search capabilities

3. **Automated Email Reports**
   - Per-session email sent to admin after processing
   - Includes: session details, tutor reschedule rate, risk flags, key insights
   - Formatted for quick scanning

4. **Session Processing Pipeline**
   - Accept session data via API
   - Process sessions asynchronously
   - Update tutor scores in real-time
   - Handle 3,000 sessions/day with 1-hour latency requirement

5. **Synthetic Data Generation**
   - Generate realistic tutor and session data
   - Include reschedule patterns for testing
   - Historical data for trend analysis

#### Technical Requirements
- RESTful API (FastAPI) for session ingestion and dashboard queries
- PostgreSQL database for data persistence
- Background job processing (Celery/Redis)
- React dashboard for visualization
- Email service integration (SendGrid/SES)
- Deployment on Render (MVP), AWS-ready architecture

### 3.2 Out of Scope (Future Phases)

1. **AI-Powered Pattern Analysis** (Phase 2)
   - LLM analysis of reschedule reasons
   - Pattern detection in tutor behavior

2. **No-Show Risk Prediction** (Phase 2)
   - Predictive model for no-show likelihood
   - Early warning system

3. **First Session Quality Scoring** (Phase 3)
   - LLM analysis of session transcripts
   - Sentiment and engagement analysis

4. **Real Rails Integration** (Production)
   - MVP uses mock integration
   - Production will have full Rails API integration

5. **Real-Time Alerts** (Future)
   - Push notifications
   - Slack/Teams integration

---

## 4. User Stories

### 4.1 Administrator User Stories

**US-1: View At-Risk Tutors**
- **As an** administrator
- **I want to** see a list of tutors with high reschedule rates
- **So that** I can prioritize coaching interventions

**US-2: Understand Tutor Performance**
- **As an** administrator
- **I want to** view detailed tutor performance metrics
- **So that** I can understand why they're flagged and what actions to take

**US-3: Receive Session Reports**
- **As an** administrator
- **I want to** receive automated email reports after each session
- **So that** I'm informed about tutor performance without checking the dashboard

**US-4: Track Trends**
- **As an** administrator
- **I want to** see reschedule rate trends over time
- **So that** I can identify if interventions are working

### 4.2 System User Stories

**US-5: Process Sessions Automatically**
- **As the** system
- **I want to** process sessions asynchronously
- **So that** I can handle 3,000 daily sessions without blocking

**US-6: Calculate Reschedule Rates**
- **As the** system
- **I want to** calculate reschedule rates accurately
- **So that** I can flag at-risk tutors reliably

---

## 5. Functional Requirements

### 5.1 Reschedule Rate Calculation

**FR-1: Reschedule Rate Formula**
- Calculate: `(Tutor-Initiated Reschedules / Total Sessions) * 100`
- Time windows: 7-day, 30-day, 90-day rolling averages
- Threshold: Flag tutors with >15% reschedule rate (configurable)

**FR-2: Reschedule Tracking**
- Track each reschedule event with:
  - Original session time
  - New session time
  - Initiator (tutor vs student)
  - Reason (if available)
  - Time between cancellation and reschedule

**FR-3: Risk Flagging**
- Automatically flag tutors exceeding threshold
- Update risk status in real-time as sessions are processed
- Maintain historical risk status for trend analysis

### 5.2 Dashboard Requirements

**FR-4: Tutor List View**
- Display all tutors with:
  - Tutor ID/Name
  - Current reschedule rate
  - Risk flag indicator
  - Total sessions
  - Last updated timestamp
- Sortable by: reschedule rate, risk flag, total sessions
- Filterable by: risk status, time period

**FR-5: Tutor Detail View**
- Show individual tutor metrics:
  - Reschedule rate over time (chart)
  - Recent reschedule events (list)
  - Session history summary
  - Risk trend indicators
- Include actionable insights/recommendations

**FR-6: Dashboard Performance**
- Load dashboard data within 2 seconds
- Support real-time updates (polling every 30 seconds)
- Handle 100+ tutors without performance degradation

### 5.3 Email Reporting

**FR-7: Per-Session Email Report**
- Send email within 1 hour of session completion
- Include:
  - Session details (ID, date, tutor, student)
  - Tutor's current reschedule rate
  - Risk flag status
  - Key insights (e.g., "Tutor has rescheduled 3 times in past 7 days")
  - Link to dashboard for full details

**FR-8: Email Format**
- HTML email with clear formatting
- Mobile-responsive design
- Quick-scan format (most important info at top)

### 5.4 API Requirements

**FR-9: Session Ingestion API**
- Endpoint: `POST /api/sessions`
- Accepts session data:
  ```json
  {
    "session_id": "string",
    "tutor_id": "string",
    "student_id": "string",
    "scheduled_time": "datetime",
    "completed_time": "datetime",
    "status": "completed|rescheduled|no_show",
    "reschedule_info": {
      "initiator": "tutor|student",
      "reason": "string",
      "original_time": "datetime",
      "new_time": "datetime"
    }
  }
  ```
- Returns: `202 Accepted` (async processing)
- Validates input data

**FR-10: Dashboard Data API**
- Endpoint: `GET /api/tutors`
  - Returns list of tutors with scores
  - Supports filtering and sorting
- Endpoint: `GET /api/tutors/{id}`
  - Returns detailed tutor information
- Endpoint: `GET /api/tutors/{id}/history`
  - Returns historical reschedule data

### 5.5 Data Processing

**FR-11: Async Processing**
- Process sessions in background queue
- Retry failed jobs (3 attempts with exponential backoff)
- Log all processing events
- Handle 3,000 sessions/day with 1-hour max latency

**FR-12: Data Consistency**
- Ensure atomic updates to tutor scores
- Handle concurrent session processing
- Maintain data integrity during failures

---

## 6. Non-Functional Requirements

### 6.1 Performance
- **Processing Latency**: 1 hour maximum from session completion to insights
- **API Response Time**: <500ms for dashboard queries
- **Dashboard Load Time**: <2 seconds
- **Throughput**: Handle 3,000 sessions/day (peak ~125/hour)

### 6.2 Reliability
- **Uptime**: 99% availability for MVP
- **Error Handling**: Graceful degradation, no data loss
- **Job Processing**: Retry mechanism for failed jobs

### 6.3 Scalability
- **Architecture**: Designed to scale horizontally
- **Database**: Indexed for efficient queries
- **Queue**: Can handle burst loads

### 6.4 Security
- **API Authentication**: JWT tokens or API keys
- **Data Protection**: Encrypt sensitive data at rest
- **Input Validation**: Sanitize all user inputs

### 6.5 Usability
- **Dashboard**: Intuitive, clean design
- **Mobile Responsive**: Dashboard works on mobile devices
- **Accessibility**: Basic WCAG compliance

---

## 7. Technical Architecture

### 7.1 Backend Stack
- **API Framework**: FastAPI (Python)
- **Task Queue**: Celery with Redis broker
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Email**: SendGrid or AWS SES

### 7.2 Frontend Stack
- **Framework**: React
- **State Management**: React Query or Context API
- **Charts**: Recharts
- **HTTP Client**: Axios

### 7.3 Infrastructure (MVP)
- **Backend**: Render (Web Service)
- **Workers**: Render (Background Workers)
- **Database**: Render (PostgreSQL)
- **Cache/Queue**: Render (Redis)
- **Frontend**: Static hosting (Render or AWS S3)

### 7.4 Data Model

**Tables:**
- `tutors` - Tutor profile and metadata
- `sessions` - Session records
- `reschedules` - Reschedule event tracking
- `tutor_scores` - Calculated risk scores and flags
- `email_reports` - Email report history

---

## 8. Data Requirements

### 8.1 Synthetic Data to Generate

**Tutor Data:**
- 50-100 tutors with varied profiles
- Historical session counts (realistic distribution)
- Reschedule patterns (some high-risk, some low-risk)

**Session Data:**
- 3,000+ sessions over past 90 days
- Mix of completed, rescheduled, no-show statuses
- Realistic timestamps and durations
- Tutor-initiated reschedules (98.2% of total reschedules)

**Reschedule Data:**
- Reschedule events with:
  - Original and new session times
  - Initiator (mostly tutor)
  - Reason codes (personal, emergency, etc.)
  - Time patterns (last-minute vs planned)

### 8.2 Data Quality
- Realistic distributions (not uniform random)
- Temporal patterns (busier times, trends)
- Correlations (high-reschedule tutors have patterns)

---

## 9. Success Metrics

### 9.1 Technical Metrics
- ✅ Processes 3,000 sessions/day successfully
- ✅ 1-hour processing latency maintained
- ✅ 99%+ job processing success rate
- ✅ Dashboard loads in <2 seconds

### 9.2 Business Metrics
- ✅ Identifies high-reschedule tutors accurately
- ✅ Provides actionable insights in email reports
- ✅ Dashboard enables quick identification of at-risk tutors

### 9.3 Demo Metrics
- ✅ Can showcase working system in 5 minutes
- ✅ Demonstrates clear business value
- ✅ Shows production-readiness potential

---

## 10. Risks and Mitigations

### 10.1 Technical Risks
- **Risk**: Processing latency exceeds 1 hour
  - **Mitigation**: Optimize database queries, scale workers
- **Risk**: Data inconsistencies during concurrent processing
  - **Mitigation**: Use database transactions, proper locking
- **Risk**: Email delivery failures
  - **Mitigation**: Retry mechanism, fallback notification

### 10.2 Business Risks
- **Risk**: Threshold too high/low (misses at-risk tutors or too many false positives)
  - **Mitigation**: Make threshold configurable, test with synthetic data
- **Risk**: Dashboard doesn't provide actionable insights
  - **Mitigation**: Include specific recommendations, link to detailed views

---

## 11. Future Phases

### Phase 2: Enhanced Intelligence
- No-show risk prediction model
- AI-powered reschedule pattern analysis (OpenAI)
- Enhanced dashboard with predictive insights

### Phase 3: First Session Quality
- LLM analysis of session transcripts
- Sentiment and engagement scoring
- First session quality dashboard

### Phase 4: Production Integration
- Full Rails API integration
- Real-time webhooks
- Advanced monitoring and alerting
- AWS migration for scale

---

## 12. Open Questions

1. What is the exact threshold for "high reschedule rate"? (Starting with 15%, will validate)
2. Who are the email recipients? (Admin users, configurable)
3. What session data is available from Rails app? (Will mock for MVP)
4. How should risk scores be calculated? (Starting simple, can enhance)

---

## 13. Approval and Sign-off

**Status**: Ready for Implementation  
**Next Steps**: 
1. Review architecture
2. Set up project structure
3. Begin synthetic data generation
4. Build MVP components

