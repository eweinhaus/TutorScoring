# AI Tools Documentation
## Tutor Quality Scoring System

**Last Updated:** 2024  
**Project Phase:** MVP Complete, AI Features Planned for Phase 2-3

---

## Executive Summary

This document outlines the AI tools and strategies planned for the Tutor Quality Scoring System. The MVP (Phase 1) focuses on foundational infrastructure and rule-based scoring, while Phase 2-3 will introduce sophisticated AI-powered analysis using OpenAI's GPT-4 API.

**Current State:** MVP does not use AI tools (by design)  
**Future State:** AI features planned for Phase 2-3 (Weeks 3-8)

---

## AI Tool Selection

### Primary AI Provider: OpenAI GPT-4

**Decision Rationale:**
- **Sophistication:** GPT-4 provides advanced reasoning capabilities for pattern analysis
- **Reliability:** Proven API with excellent uptime and support
- **Cost-Effectiveness:** Competitive pricing with pay-per-use model
- **Flexibility:** Supports various analysis tasks (categorization, sentiment, pattern detection)

**Alternative Considered:**
- **Anthropic Claude:** Not selected due to OpenAI's broader ecosystem and established patterns

### Model Selection

**GPT-4 (gpt-4-turbo-preview)**
- **Use Case:** Complex pattern analysis, reschedule reason categorization, session quality scoring
- **Rationale:** Best-in-class reasoning for nuanced analysis
- **Cost:** ~$0.01-0.03 per session analysis

**GPT-3.5-turbo (Future Optimization)**
- **Use Case:** Simple categorization tasks, lower-cost operations
- **Rationale:** 10x cheaper for straightforward tasks
- **Cost:** ~$0.001 per simple analysis

---

## Phase 2: AI-Powered Reschedule Pattern Analysis

### Feature Overview

**Problem Statement:** 
Currently, the system tracks *how often* tutors reschedule, but not *why*. Understanding reschedule patterns is critical for targeted coaching interventions.

**AI Solution:**
Use GPT-4 to analyze reschedule reason text and extract actionable insights.

### Implementation Strategy

#### 1. Reschedule Reason Categorization

**Prompting Strategy:**
```
You are analyzing tutor reschedule reasons to identify patterns and coaching opportunities.

Reschedule reason: "{reschedule_reason_text}"

Analyze this reschedule reason and provide:
1. Category: [Personal Emergency | Scheduling Conflict | Health Issue | Student Request | Other]
2. Urgency Level: [High | Medium | Low]
3. Pattern Indicator: [Recurring Pattern | One-Time Event | Unclear]
4. Sentiment: [Professional | Apologetic | Frustrated | Neutral]
5. Coaching Insight: [Brief recommendation for addressing this pattern]

Format as JSON:
{
  "category": "...",
  "urgency": "...",
  "pattern": "...",
  "sentiment": "...",
  "coaching_insight": "..."
}
```

**Expected Output:**
- Categorized reschedule reasons for dashboard visualization
- Pattern detection across tutor behavior
- Sentiment analysis for early intervention signals

**Cost Estimate:**
- ~$0.01 per reschedule analysis
- 3,000 sessions/day × 30% reschedule rate = 900 analyses/day
- Monthly cost: ~$270/month
- **Optimization:** Batch similar reasons, cache common patterns → **~$50-100/month**

#### 2. Pattern Detection Across Tutor Behavior

**Prompting Strategy:**
```
Analyze the following reschedule history for tutor {tutor_id}:

Reschedule Events:
{json_array_of_reschedule_events}

Identify:
1. Temporal patterns (e.g., "Frequently reschedules on Fridays")
2. Reason patterns (e.g., "Consistently cites personal emergencies")
3. Frequency trends (increasing, decreasing, stable)
4. Risk indicators (early warning signs of churn)

Provide actionable coaching recommendations.
```

**Expected Output:**
- Pattern insights displayed in dashboard
- Automated coaching recommendations
- Risk adjustments based on pattern quality

**Cost Estimate:**
- ~$0.02 per tutor analysis (run weekly)
- 578 tutors × 4 analyses/month = 2,312 analyses/month
- Monthly cost: ~$46/month
- **Optimization:** Only analyze tutors with recent reschedules → **~$20/month**

### Integration Points

**Backend Service:**
- New service: `app/services/ai_analysis_service.py`
- Integration with existing `reschedule_calculator.py`
- Async processing via Celery tasks

**Database Schema:**
- New table: `ai_insights`
  - `tutor_id` (FK)
  - `insight_type` (pattern, sentiment, category)
  - `insight_data` (JSON)
  - `generated_at` (timestamp)

**Dashboard Updates:**
- New component: `AIInsightsPanel`
- Reschedule reason breakdown (pie chart)
- Pattern visualization (timeline)
- Coaching recommendations panel

---

## Phase 3: First Session Quality Scoring

### Feature Overview

**Problem Statement:**
24% of churners fail at first session experiences. Need to detect and score session quality using AI analysis of session transcripts.

### Implementation Strategy

#### LLM-Based Session Quality Analysis

**Prompting Strategy:**
```
You are analyzing a tutoring session transcript to evaluate session quality.

Session Transcript:
{transcript_text}

Tutor: {tutor_name}
Student: {student_id}
Session Type: First Session | Follow-up

Evaluate this session across multiple dimensions:

1. Engagement Level (1-10):
   - Tutor engagement and enthusiasm
   - Student responsiveness and participation
   
2. Communication Clarity (1-10):
   - Tutor explanation quality
   - Student comprehension indicators
   
3. Preparation Quality (1-10):
   - Tutor preparation and organization
   - Lesson structure and flow
   
4. Student Engagement Indicators (1-10):
   - Questions asked
   - Active participation
   - Interest level
   
5. Overall Session Quality (1-10):
   - Composite score

Provide:
- Numerical scores for each dimension
- Key strengths (top 3)
- Areas for improvement (top 3)
- Specific coaching recommendations (3-5 actionable items)
- Risk assessment: [Low Risk | Medium Risk | High Risk]

Format as JSON:
{
  "scores": {
    "engagement": 8,
    "communication": 7,
    "preparation": 9,
    "student_engagement": 6,
    "overall": 7.5
  },
  "strengths": ["...", "...", "..."],
  "improvements": ["...", "...", "..."],
  "recommendations": ["...", "...", "..."],
  "risk_level": "..."
}
```

**Expected Output:**
- Session quality score (1-100)
- Dimensional breakdowns
- Specific strengths and weaknesses
- Actionable coaching recommendations
- Risk flag for poor first sessions (<60 score)

**Cost Estimate:**
- ~$0.01-0.03 per transcript analysis
- 3,000 sessions/day × 20% first sessions = 600 analyses/day
- Monthly cost: ~$180-540/month
- **Optimization:** Batch processing, cache similar patterns → **~$90-270/month**

### Integration Points

**Backend Service:**
- New service: `app/services/session_quality_service.py`
- Integration with `session_processor.py`
- Transcript ingestion from Rails app or manual upload

**Database Schema:**
- New table: `session_quality_scores`
  - `session_id` (FK)
  - `engagement_score`, `communication_score`, etc. (DECIMAL)
  - `overall_score` (DECIMAL)
  - `strengths` (JSON array)
  - `improvements` (JSON array)
  - `recommendations` (JSON array)
  - `risk_level` (VARCHAR)
  - `ai_analysis_raw` (JSON)

**Dashboard Updates:**
- First session quality dashboard
- Quality score trends over time
- Comparison: first sessions vs. follow-ups
- Coaching recommendations panel

---

## Prompting Strategies & Best Practices

### 1. Structured Output Format

**Why:** Consistent JSON responses enable reliable parsing and database storage.

**Pattern:**
```python
prompt = f"""
Analyze: {input_data}

Provide structured JSON:
{{
  "category": "...",
  "score": number,
  "insights": ["...", "..."],
  "recommendations": ["...", "..."]
}}
"""
```

### 2. Few-Shot Examples

**Why:** Examples guide the model to produce desired output format and quality.

**Pattern:**
```python
prompt = f"""
Examples:

Example 1:
Input: "Family emergency, need to reschedule"
Output: {{
  "category": "Personal Emergency",
  "urgency": "High",
  "pattern": "One-Time Event",
  "sentiment": "Professional"
}}

Example 2:
Input: "Can't make it Friday again"
Output: {{
  "category": "Scheduling Conflict",
  "urgency": "Medium",
  "pattern": "Recurring Pattern",
  "sentiment": "Neutral"
}}

Now analyze: {reschedule_reason}
"""
```

### 3. Context Injection

**Why:** Providing tutor history and session context improves analysis accuracy.

**Pattern:**
```python
prompt = f"""
Tutor Context:
- Total Sessions: {total_sessions}
- Recent Reschedules: {recent_reschedules}
- Average Score: {avg_score}

Reschedule Reason: {reason}
Temporal Pattern: {pattern}

Analyze with context...
"""
```

### 4. Cost Optimization Techniques

**Batch Processing:**
- Group multiple analyses in single API call
- Use `n` parameter for parallel completions
- Reduces API overhead

**Caching:**
- Cache similar analyses (e.g., identical reschedule reasons)
- Use Redis for temporary caching
- Reduces redundant API calls

**Model Selection:**
- Use GPT-4 for complex analysis
- Use GPT-3.5-turbo for simple categorization
- Reduces cost by 10x for simple tasks

**Rate Limiting:**
- Implement exponential backoff
- Respect API rate limits
- Queue requests during high load

### 5. Error Handling

**Retry Logic:**
```python
@celery_app.task(bind=True, max_retries=3)
def analyze_reschedule_reason(self, reschedule_id):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,  # Lower temperature for consistent results
            max_tokens=500
        )
        return parse_response(response)
    except openai.RateLimitError:
        raise self.retry(exc=exc, countdown=60)  # Retry after 60s
    except openai.APIError as e:
        log_error(e)
        raise self.retry(exc=exc, countdown=300)  # Retry after 5min
```

**Fallback Strategies:**
- If AI analysis fails, use rule-based categorization
- Cache successful analyses for similar patterns
- Log failures for manual review

---

## Cost Management Strategy

### Cost Optimization Techniques

1. **Batch Processing**
   - Group multiple analyses in single API call
   - Process during off-peak hours
   - Estimated savings: 30-40%

2. **Caching**
   - Cache identical or similar reschedule reasons
   - Cache tutor pattern analyses (TTL: 7 days)
   - Estimated savings: 20-30%

3. **Model Selection**
   - Use GPT-4 for complex analysis (session quality)
   - Use GPT-3.5-turbo for simple tasks (categorization)
   - Estimated savings: 50-70% for simple tasks

4. **Selective Processing**
   - Only analyze high-risk tutors
   - Skip analysis for tutors with <5 sessions
   - Estimated savings: 10-20%

### Cost Monitoring

**Metrics to Track:**
- API calls per day
- Cost per session
- Cost per tutor
- Cache hit rate
- Error rate

**Alerting Thresholds:**
- Daily cost > $15 (50% over budget)
- API error rate > 5%
- Cache hit rate < 60%

---

## Implementation Timeline

### Phase 2 (Weeks 3-5): Reschedule Pattern Analysis

**Week 3:**
- Set up OpenAI API integration
- Implement reschedule reason categorization
- Create `ai_analysis_service.py`
- Add database schema for AI insights

**Week 4:**
- Implement pattern detection across tutor behavior
- Create Celery tasks for async processing
- Add caching layer
- Dashboard integration

**Week 5:**
- Testing and optimization
- Cost monitoring setup
- Performance validation
- Documentation

### Phase 3 (Weeks 6-8): First Session Quality Scoring

**Week 6:**
- Implement transcript ingestion
- Create session quality analysis service
- Design prompting strategy for quality scoring
- Database schema for quality scores

**Week 7:**
- Dashboard integration
- First session pattern detection
- Coaching recommendations
- Testing

**Week 8:**
- Performance optimization
- Cost optimization
- Documentation
- User acceptance testing

---

## Risk Mitigation

### Technical Risks

**AI API Availability:**
- **Risk:** OpenAI API downtime
- **Mitigation:** Fallback to rule-based categorization, queue requests

**Cost Overruns:**
- **Risk:** Unexpected API costs
- **Mitigation:** Rate limiting, cost monitoring, alerting

**Model Accuracy:**
- **Risk:** AI produces incorrect insights
- **Mitigation:** Human review for high-risk cases, confidence scoring

### Business Risks

**False Positives:**
- **Risk:** AI flags tutors incorrectly
- **Mitigation:** Confidence thresholds, human review, feedback loop

**User Adoption:**
- **Risk:** Administrators don't trust AI insights
- **Mitigation:** Explainable AI, show reasoning, gradual rollout

---

## Success Metrics

### Technical Metrics
- AI analysis accuracy: >85% categorization accuracy
- Processing latency: <5 seconds per analysis
- Cost per session: <$0.02 average
- Cache hit rate: >60%

### Business Metrics
- Coaching recommendations adoption rate: >70%
- Improvement in tutor performance after coaching: >15%
- Reduction in churn for at-risk tutors: >20%
- Administrator satisfaction with AI insights: >80%

---

## Future Enhancements

### Advanced AI Features (Phase 5+)

1. **Predictive Churn Modeling**
   - Multi-factor churn prediction
   - Early intervention system
   - ML model training on historical data

2. **Personalized Coaching Plans**
   - AI-generated personalized coaching plans
   - Learning paths for tutors
   - Progress tracking

3. **Natural Language Interface**
   - Chat interface for administrators
   - "Why is this tutor at risk?"
   - "What should I do about high reschedule rates?"

4. **Vector Search & Similarity**
   - Find similar tutors for cohort analysis
   - Identify tutors with similar patterns
   - Recommendations based on successful interventions

---

## Conclusion

The Tutor Quality Scoring System is designed with AI integration in mind, but the MVP focuses on foundational infrastructure. Phase 2-3 will introduce sophisticated AI-powered analysis using OpenAI's GPT-4 API, with careful attention to cost optimization, error handling, and business value.

**Key Takeaways:**
- MVP: Rule-based scoring (no AI)
- Phase 2: AI-powered reschedule pattern analysis
- Phase 3: LLM-based first session quality scoring
- Cost optimization: Batch processing, caching, model selection
- Success: Measurable improvements in tutor retention and coaching effectiveness

---

## References

- OpenAI API Documentation: https://platform.openai.com/docs
- GPT-4 Technical Report: https://openai.com/research/gpt-4
- Cost Calculator: https://openai.com/pricing
- Best Practices: https://platform.openai.com/docs/guides/prompt-engineering

