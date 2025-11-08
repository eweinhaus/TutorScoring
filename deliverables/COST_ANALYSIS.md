# Cost Analysis
## Tutor Quality Scoring System

**Last Updated:** 2024  
**Project Phase:** MVP Complete, Production Deployment Planned  
**Scale:** 3,000 sessions/day (90,000 sessions/month)

---

## Executive Summary

This document provides a comprehensive cost analysis for the Tutor Quality Scoring System across three deployment phases:
1. **MVP (Render)** - Current deployment platform
2. **Production (AWS)** - Production-scale infrastructure
3. **Future Phases (AI-Enhanced)** - With AI features enabled

**Key Findings:**
- MVP costs: **~$60/month** (Render)
- Production costs: **~$400-700/month** (AWS, without AI)
- Production with AI: **~$600-1,100/month** (AWS + OpenAI API)
- Cost per session: **$0.0007** (MVP) to **$0.012** (Production with AI)

---

## MVP Costs (Render Platform)

### Current Infrastructure

**Services:**
- **Web Service (API):** FastAPI application
  - Plan: Starter ($7/month) or Standard ($25/month)
  - Recommended: Standard for production-like performance
  - Cost: **$25/month**

- **Background Worker:** Celery worker service
  - Plan: Starter ($7/month) or Standard ($15/month)
  - Recommended: Standard for 3K sessions/day capacity
  - Cost: **$15/month**

- **PostgreSQL Database:** Managed database
  - Plan: Starter ($7/month) or Standard ($20/month)
  - Recommended: Standard for 3K sessions/day capacity
  - Cost: **$20/month**

- **Redis (Key Value):** Managed Redis instance
  - Plan: Free tier (25MB) or Starter ($5/month)
  - Recommended: Starter for production capacity
  - Cost: **$5/month** (or $0 if free tier sufficient)

- **Static Site (Frontend):** React dashboard
  - Plan: Free tier (unlimited sites)
  - Cost: **$0/month**

**Total MVP Costs:**
- Minimum (Free tier where possible): **~$47/month**
- Recommended (Standard tier): **~$65/month**
- **Average: ~$60/month**

### Cost Breakdown by Component

| Component | Plan | Monthly Cost | Notes |
|-----------|------|--------------|-------|
| Web Service | Standard | $25 | FastAPI API server |
| Worker | Standard | $15 | Celery background workers |
| PostgreSQL | Standard | $20 | Managed database |
| Redis | Starter | $5 | Message queue & cache |
| Frontend | Free | $0 | Static site hosting |
| **Total** | | **$65** | |

### Scaling Considerations

**Render Free Tier Limitations:**
- Services spin down after 15 minutes of inactivity
- Cold starts: 30-60 seconds
- Not suitable for production SLA requirements

**Recommended Upgrade Path:**
- Start with Standard tier for all services
- Upgrade to Pro tier if needed for higher throughput
- Pro tier: ~$50-100/month per service

---

## Production Costs (AWS Platform)

### Infrastructure Components

#### 1. Compute (API & Workers)

**Option A: AWS ECS Fargate (Recommended)**
- **API Service:**
  - Task: 0.5 vCPU, 1GB RAM
  - Cost: ~$0.04/hour × 730 hours = **$29/month**
  - Auto-scaling: 1-3 tasks based on load
  - **Estimated: $30-60/month**

- **Worker Service:**
  - Task: 0.25 vCPU, 512MB RAM
  - Cost: ~$0.02/hour × 730 hours = **$15/month**
  - Auto-scaling: 1-2 tasks based on queue depth
  - **Estimated: $15-30/month**

**Option B: EC2 Instances**
- **API Server:**
  - Instance: t3.small (2 vCPU, 2GB RAM)
  - Cost: ~$0.0208/hour × 730 hours = **$15/month**
  - **Estimated: $15-30/month** (with auto-scaling)

- **Worker Instance:**
  - Instance: t3.micro (2 vCPU, 1GB RAM)
  - Cost: ~$0.0104/hour × 730 hours = **$8/month**
  - **Estimated: $8-15/month**

**Recommended:** ECS Fargate for flexibility and cost efficiency  
**Total Compute: $50-90/month**

#### 2. Database (PostgreSQL)

**AWS RDS PostgreSQL:**
- **Instance:** db.t3.micro (2 vCPU, 1GB RAM) - Development
  - Cost: ~$0.017/hour × 730 hours = **$12/month**
  - Storage: 20GB GP3 SSD = **$2/month**
  - Backup storage: 5GB = **$1/month**
  - **Total: $15/month**

- **Instance:** db.t3.small (2 vCPU, 2GB RAM) - Production
  - Cost: ~$0.034/hour × 730 hours = **$25/month**
  - Storage: 100GB GP3 SSD = **$10/month**
  - Backup storage: 20GB = **$2/month**
  - Multi-AZ (for HA): Double cost
  - **Total: $37/month** (single-AZ) or **$74/month** (Multi-AZ)

**Recommended:** db.t3.small with Multi-AZ for production  
**Total Database: $80-120/month**

#### 3. Cache & Queue (Redis)

**AWS ElastiCache for Redis:**
- **Instance:** cache.t3.micro (0.5GB RAM)
  - Cost: ~$0.017/hour × 730 hours = **$12/month**
  - **Estimated: $12-20/month**

**Alternative: AWS SQS (Simple Queue Service)**
- Cost: First 1M requests free, then $0.40 per 1M requests
- 3K sessions/day = 90K/month = **$0/month** (within free tier)
- **Recommended for queue:** SQS for cost savings

**Recommended:** ElastiCache for Redis (caching + queue)  
**Total Cache/Queue: $12-20/month**

#### 4. Storage & CDN

**AWS S3 (Frontend Static Hosting):**
- Storage: 1GB = **$0.023/month**
- Requests: 100K/month = **$0.40/month**
- **Total: ~$1/month**

**AWS CloudFront (CDN):**
- Data transfer: 10GB/month = **$0.85/month**
- Requests: 100K/month = **$0.10/month**
- **Total: ~$1/month**

**Total Storage/CDN: $2-5/month**

#### 5. Networking

**Data Transfer:**
- Egress: 10GB/month = **$0.90/month**
- Inter-service (within VPC): **$0/month**
- **Total: ~$1-5/month**

**Load Balancer:**
- Application Load Balancer (ALB)
- Cost: ~$0.0225/hour × 730 hours = **$16/month**
- Data processing: **$0.008/GB** (minimal)
- **Total: ~$20/month**

**Total Networking: $20-30/month**

#### 6. Monitoring & Logging

**AWS CloudWatch:**
- Logs: 5GB/month = **$0.50/month**
- Metrics: 50 custom metrics = **$0.30/month**
- Alarms: 10 alarms = **$0.10/month**
- **Total: ~$1-5/month**

**Total Monitoring: $1-5/month**

### AWS Production Cost Summary

| Component | Monthly Cost | Notes |
|-----------|--------------|-------|
| Compute (ECS/EC2) | $50-90 | API + Workers |
| Database (RDS) | $80-120 | PostgreSQL Multi-AZ |
| Cache/Queue (ElastiCache) | $12-20 | Redis |
| Storage/CDN (S3 + CloudFront) | $2-5 | Frontend hosting |
| Networking (ALB + Data Transfer) | $20-30 | Load balancer |
| Monitoring (CloudWatch) | $1-5 | Logs & metrics |
| **Total** | **$165-270** | Without AI features |

**Recommended Production Setup:**
- ECS Fargate: $60/month
- RDS Multi-AZ: $100/month
- ElastiCache: $15/month
- S3 + CloudFront: $3/month
- ALB: $20/month
- CloudWatch: $2/month
- **Total: ~$200/month**

---

## AI Features Costs (Phase 2-3)

### OpenAI API Costs

#### Phase 2: Reschedule Pattern Analysis

**Reschedule Reason Categorization:**
- Model: GPT-4-turbo-preview
- Input: ~200 tokens per reschedule reason
- Output: ~300 tokens per analysis
- Cost: $0.01/1K input tokens, $0.03/1K output tokens
- **Cost per analysis: ~$0.011**
- Volume: 3,000 sessions/day × 30% reschedule rate = 900 analyses/day
- Daily cost: $9.90
- **Monthly cost: $297**

**Optimization (Batch Processing + Caching):**
- Batch 10 analyses per API call: -20% overhead
- Cache identical reasons: -30% redundant calls
- **Optimized monthly cost: ~$150**

**Pattern Detection (Weekly Analysis):**
- Model: GPT-4-turbo-preview
- Input: ~1,000 tokens per tutor
- Output: ~500 tokens per analysis
- Cost per analysis: ~$0.025
- Volume: 578 tutors × 4 analyses/month = 2,312 analyses/month
- **Monthly cost: $58**

**Optimization (Selective Processing):**
- Only analyze high-risk tutors (30%): -70% volume
- **Optimized monthly cost: ~$20**

**Phase 2 Total AI Costs:**
- Without optimization: **$355/month**
- With optimization: **~$170/month**

#### Phase 3: First Session Quality Scoring

**Session Transcript Analysis:**
- Model: GPT-4-turbo-preview
- Input: ~2,000 tokens per transcript (average session)
- Output: ~800 tokens per analysis
- Cost: $0.01/1K input tokens, $0.03/1K output tokens
- **Cost per analysis: ~$0.044**
- Volume: 3,000 sessions/day × 20% first sessions = 600 analyses/day
- Daily cost: $26.40
- **Monthly cost: $792**

**Optimization (Batch Processing + Caching):**
- Batch 5 analyses per API call: -15% overhead
- Cache similar patterns: -20% redundant calls
- Use GPT-3.5-turbo for simple sessions: -70% cost for 30% of sessions
- **Optimized monthly cost: ~$270**

**Phase 3 Total AI Costs:**
- Without optimization: **$792/month**
- With optimization: **~$270/month**

### Combined AI Costs (Phase 2 + Phase 3)

**Full AI Implementation:**
- Phase 2: $170/month (optimized)
- Phase 3: $270/month (optimized)
- **Total: $440/month**

**Without Optimization:**
- Phase 2: $355/month
- Phase 3: $792/month
- **Total: $1,147/month**

**Recommended:** Optimized approach with batch processing, caching, and selective model usage  
**Estimated AI Costs: $200-400/month**

---

## Total Cost Projections

### Scenario 1: MVP (Current - Render)

| Component | Monthly Cost |
|-----------|-------------|
| Infrastructure (Render) | $60 |
| AI Features | $0 |
| **Total** | **$60** |

### Scenario 2: Production (AWS, No AI)

| Component | Monthly Cost |
|-----------|-------------|
| Infrastructure (AWS) | $200 |
| AI Features | $0 |
| **Total** | **$200** |

### Scenario 3: Production (AWS, With AI)

| Component | Monthly Cost |
|-----------|-------------|
| Infrastructure (AWS) | $200 |
| AI Features (Optimized) | $350 |
| **Total** | **$550** |

### Scenario 4: Production (AWS, Full AI, No Optimization)

| Component | Monthly Cost |
|-----------|-------------|
| Infrastructure (AWS) | $200 |
| AI Features (Full) | $1,147 |
| **Total** | **$1,347** |

---

## Cost Per Session Analysis

### MVP (Render)
- Monthly sessions: 90,000
- Monthly cost: $60
- **Cost per session: $0.0007**

### Production (AWS, No AI)
- Monthly sessions: 90,000
- Monthly cost: $200
- **Cost per session: $0.0022**

### Production (AWS, With AI)
- Monthly sessions: 90,000
- Monthly cost: $550
- **Cost per session: $0.0061**

### Production (AWS, Full AI)
- Monthly sessions: 90,000
- Monthly cost: $1,347
- **Cost per session: $0.015**

---

## Cost Optimization Strategies

### 1. Infrastructure Optimization

**Reserved Instances (RDS):**
- 1-year commitment: 30-40% savings
- Estimated savings: $30-40/month on RDS

**Spot Instances (Workers):**
- Use spot instances for Celery workers (can tolerate interruption)
- Estimated savings: 60-70% on compute
- Estimated savings: $20-30/month

**S3 Lifecycle Policies:**
- Move old logs to Glacier (cheaper storage)
- Estimated savings: $5-10/month

**Total Infrastructure Savings: $55-80/month**

### 2. AI API Optimization

**Batch Processing:**
- Group multiple analyses in single API call
- Estimated savings: 20-30%

**Caching:**
- Cache identical or similar analyses
- Estimated savings: 20-30%

**Model Selection:**
- Use GPT-3.5-turbo for simple tasks
- Use GPT-4 only for complex analysis
- Estimated savings: 50-70% for simple tasks

**Selective Processing:**
- Only analyze high-risk tutors
- Skip analysis for tutors with <5 sessions
- Estimated savings: 10-20%

**Total AI Savings: $150-300/month**

### 3. Scaling Optimization

**Auto-Scaling:**
- Scale workers based on queue depth
- Scale API based on request rate
- Pay only for what you use

**Database Optimization:**
- Use read replicas for dashboard queries
- Primary database for writes only
- Estimated savings: Distribute load, improve performance

---

## Cost Comparison: MVP vs Production

| Metric | MVP (Render) | Production (AWS) |
|--------|-------------|------------------|
| **Monthly Cost (No AI)** | $60 | $200 |
| **Monthly Cost (With AI)** | $60 | $550 |
| **Cost per Session (No AI)** | $0.0007 | $0.0022 |
| **Cost per Session (With AI)** | $0.0007 | $0.0061 |
| **Scalability** | Limited | High |
| **Reliability** | Good | Excellent |
| **Uptime SLA** | 99.9% | 99.99% |
| **Setup Complexity** | Low | Medium |
| **Management Overhead** | Low | Medium |

---

## ROI Analysis

### Business Value

**Tutor Retention:**
- Current churn rate: ~15% annually
- Target reduction: 20% (with system)
- Value per retained tutor: $500/month
- 578 tutors × 20% reduction × $500 = **$5,780/month value**

**Administrative Time Savings:**
- Manual monitoring: 2 hours/day
- Automated system: 0.5 hours/day
- Time saved: 1.5 hours/day
- Value: $50/hour × 1.5 hours × 30 days = **$2,250/month value**

**Total Monthly Value: ~$8,030/month**

### Cost Comparison

**System Cost:**
- MVP: $60/month
- Production (with AI): $550/month

**ROI:**
- MVP: ($8,030 - $60) / $60 = **13,283% ROI**
- Production: ($8,030 - $550) / $550 = **1,360% ROI**

### Break-Even Analysis

**Break-Even Point:**
- MVP: < 1 day
- Production: < 3 days

**Payback Period:**
- MVP: < 1 day
- Production: < 3 days

---

## Budget Recommendations

### MVP Phase (Weeks 1-2)
- **Budget: $60/month**
- Platform: Render
- Focus: Core functionality, no AI

### Production Phase (Weeks 3-12)
- **Budget: $200-550/month**
- Platform: AWS
- Focus: Scale, reliability, optional AI features

### Growth Phase (Months 4+)
- **Budget: $400-700/month**
- Platform: AWS
- Focus: Full AI features, advanced analytics

---

## Cost Monitoring & Alerting

### Key Metrics to Track

1. **Daily API Costs:**
   - OpenAI API: Alert if > $15/day
   - AWS Services: Alert if > $20/day

2. **Cost per Session:**
   - Target: < $0.01/session
   - Alert if > $0.015/session

3. **Infrastructure Utilization:**
   - CPU: Alert if > 80% average
   - Memory: Alert if > 80% average
   - Database connections: Alert if > 80% of max

### Alerting Thresholds

**Cost Alerts:**
- Daily cost > $25 (50% over budget)
- Monthly cost > $800 (50% over budget)
- Cost per session > $0.015 (50% over target)

**Usage Alerts:**
- API calls > 100K/day (50% over expected)
- Database size > 100GB (approaching limit)
- Queue depth > 1,000 (processing backlog)

---

## Conclusion

The Tutor Quality Scoring System is designed to be cost-effective at scale:

- **MVP:** $60/month (Render) - Perfect for demo and initial deployment
- **Production:** $200-550/month (AWS) - Scales to 3K+ sessions/day
- **ROI:** 1,360%+ - Significant business value

**Key Recommendations:**
1. Start with MVP (Render) for validation
2. Migrate to AWS for production scale
3. Implement AI features gradually (Phase 2-3)
4. Optimize costs with batch processing, caching, and selective model usage
5. Monitor costs closely and set up alerting

**Total Estimated Cost (90-day roadmap):**
- MVP: $60/month × 2 months = $120
- Production: $550/month × 1 month = $550
- **Total: $670 for 90-day period**

This represents excellent value for a system that processes 270,000 sessions and provides actionable insights to reduce tutor churn by 20%+.

---

## Appendix: Detailed Cost Breakdowns

### AWS ECS Fargate Pricing (us-east-1)

**API Service:**
- 0.5 vCPU, 1GB RAM: $0.04048/vCPU-hour = $0.02024/hour
- Monthly: $0.02024 × 730 = $14.78/month
- With auto-scaling (1-3 tasks): $15-45/month

**Worker Service:**
- 0.25 vCPU, 512MB RAM: $0.01012/hour
- Monthly: $0.01012 × 730 = $7.39/month
- With auto-scaling (1-2 tasks): $7-15/month

### AWS RDS PostgreSQL Pricing (us-east-1)

**db.t3.small:**
- Instance: $0.034/hour × 730 = $24.82/month
- Storage (100GB GP3): $0.115/GB = $11.50/month
- Backup (20GB): $0.095/GB = $1.90/month
- Multi-AZ: Double instance cost = $49.64/month
- **Total: $63.04/month (single-AZ) or $87.86/month (Multi-AZ)**

### OpenAI API Pricing (GPT-4-turbo-preview)

**Input:**
- $0.01 per 1K tokens

**Output:**
- $0.03 per 1K tokens

**Example Calculation:**
- Reschedule analysis: 200 input tokens + 300 output tokens
- Cost: (200/1000 × $0.01) + (300/1000 × $0.03) = $0.002 + $0.009 = $0.011

### Render Pricing

**Standard Plans:**
- Web Service: $25/month
- Worker: $15/month
- PostgreSQL: $20/month
- Redis: $5/month (Starter) or $0 (Free tier)
- Static Site: $0/month (Free tier)


