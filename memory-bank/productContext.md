# Product Context
## Tutor Quality Scoring System

---

## Why This Project Exists

### Business Problem

Tutoring platforms face significant tutor retention challenges:
- **24% of churners** fail at first session experiences
- **98.2% of reschedules** are tutor-initiated (indicating reliability issues)
- **16% of tutor replacements** are due to no-shows

Without automated systems, administrators must manually monitor thousands of sessions daily, leading to:
- Reactive rather than proactive intervention
- Limited visibility into patterns across 3,000 daily sessions
- Delayed identification of at-risk tutors
- Missed coaching opportunities

### Solution Value

An automated scoring system provides:
- **Proactive Identification:** Flag at-risk tutors before they churn
- **Data-Driven Insights:** Quantify performance patterns across all sessions
- **Actionable Intelligence:** Specific recommendations for coaching interventions
- **Scalability:** Handle 3,000+ sessions/day automatically
- **Speed:** Deliver insights within 1 hour of session completion

---

## How It Should Work

### User Journey (Administrator)

1. **Session Completes** → System automatically processes session data
2. **Background Processing** → Reschedule rates calculated, scores updated
3. **Email Report** → Admin receives per-session report with insights
4. **Dashboard View** → Admin opens dashboard to see all tutors
5. **Risk Identification** → High-risk tutors clearly flagged
6. **Detailed Analysis** → Click tutor to see detailed metrics and trends
7. **Actionable Insights** → System provides specific coaching recommendations

### Core Workflow

```
Session Data → API Ingestion → Queue → Worker Processing
    ↓
Calculate Reschedule Rates → Update Scores → Send Email
    ↓
Dashboard Displays → Admin Views → Takes Action
```

### MVP Workflow

1. **Data Ingestion:** Session data arrives via API (mock Rails integration)
2. **Async Processing:** Celery worker picks up session
3. **Score Calculation:** Reschedule rate calculated for 7-day, 30-day, 90-day windows
4. **Risk Flagging:** Tutors with >15% rate flagged as high-risk
5. **Email Report:** Automated email sent to admin with session summary
6. **Dashboard Update:** Scores available in real-time dashboard

---

## Problems It Solves

### Problem 1: High Reschedule Rates (MVP Focus)

**Problem:** Tutors with high reschedule rates indicate reliability issues but are hard to identify manually across thousands of sessions.

**Solution:** 
- Automatically calculate reschedule rate per tutor
- Flag tutors exceeding threshold (>15%)
- Track rates over multiple time windows (7d, 30d, 90d)
- Provide clear visual indicators in dashboard

**Impact:** Administrators can quickly identify and prioritize coaching for unreliable tutors.

### Problem 2: No Visibility into Patterns

**Problem:** Manual monitoring doesn't reveal patterns like "tutor always reschedules on Fridays" or "increasing trend over time."

**Solution:**
- Track all reschedule events with metadata
- Calculate trends over time
- Visualize patterns in dashboard
- Identify correlations (future: AI-powered pattern detection)

**Impact:** Administrators understand not just "who" but "why" and "when."

### Problem 3: Reactive vs Proactive Intervention

**Problem:** Issues are identified after tutors have already churned or student satisfaction is damaged.

**Solution:**
- Real-time scoring as sessions complete
- Automated email reports for immediate awareness
- Dashboard with risk flags for quick scanning
- Historical trends to identify worsening patterns

**Impact:** Administrators can intervene before issues escalate.

---

## User Experience Goals

### For Administrators

1. **Quick Scanning:** Identify at-risk tutors in seconds
2. **Deep Dive:** Understand why a tutor is flagged with detailed metrics
3. **Actionable:** Receive specific recommendations, not just data
4. **Proactive:** Get notified automatically, don't have to check manually
5. **Confidence:** Trust the system's accuracy and insights

### Dashboard Goals

- **Clean & Intuitive:** Professional appearance, easy navigation
- **Information Hierarchy:** Most important info (risk flags) most prominent
- **Visual Clarity:** Color coding, charts, clear indicators
- **Responsive:** Works on desktop and mobile
- **Fast:** Loads in <2 seconds, updates smoothly

---

## Success Metrics

### Business Metrics

- **Identification Accuracy:** Correctly identifies 80%+ of at-risk tutors
- **Intervention Rate:** Administrators take action on flagged tutors
- **Churn Reduction:** (Future) Measurable reduction in tutor churn
- **Time Savings:** Reduces manual monitoring time significantly

### User Experience Metrics

- **Dashboard Load Time:** <2 seconds
- **Email Delivery:** Within 1 hour of session completion
- **Usability:** Administrators can use dashboard without training
- **Satisfaction:** Administrators find insights valuable and actionable

---

## Future Vision

### Phase 2: Enhanced Intelligence
- No-show risk prediction
- AI-powered pattern analysis of reschedule reasons
- Predictive insights

### Phase 3: First Session Quality
- LLM analysis of session transcripts
- Sentiment and engagement scoring
- First session quality dashboard

### Phase 4: Production Integration
- Full Rails platform integration
- Real-time webhooks
- Advanced monitoring
- AWS migration

### Long-Term Vision
- Comprehensive tutor performance scoring
- Predictive churn models
- Automated coaching recommendations
- Integration with learning management systems
- Real-time alerts and notifications

---

## Key Principles

1. **Automation First:** Minimize manual work, maximize automation
2. **Actionable Insights:** Provide recommendations, not just data
3. **Real-Time:** Deliver insights quickly (1-hour SLA)
4. **Scalable:** Handle growth from 3K to 10K+ sessions/day
5. **Production-Ready:** Code quality suitable for production deployment
6. **AI-Prepared:** Architecture ready for AI/ML enhancements

