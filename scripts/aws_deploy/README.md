# AWS Deployment Automation

## 🎯 Fully Automated Deployment

This directory contains scripts for **fully automated AWS deployment** of the TutorScoring system.

## Quick Start

```bash
cd scripts/aws_deploy
./auto_deploy.sh
```

That's it! The script will:
- ✅ Check all prerequisites
- ✅ Prompt for secrets (SendGrid API Key, Admin Email)
- ✅ Auto-generate API keys
- ✅ Deploy everything automatically
- ✅ Verify deployment

## Prerequisites

The `check_prerequisites.sh` script will verify:
- AWS CLI installed and configured
- Docker installed and running
- Node.js and npm installed (for frontend)
- jq installed (recommended for JSON parsing)

## Manual Input Required

Only **2 items** need manual input:
1. **SendGrid API Key** - Enter when prompted
2. **Admin Email** - Enter when prompted

Everything else is automated!

## Scripts

### Main Script
- **auto_deploy.sh** - Master script that runs everything

### Setup Scripts
- **setup_infrastructure.sh** - VPC, subnets, security groups
- **setup_rds_redis.sh** - Database and cache
- **setup_ecr.sh** - Container registry and image push
- **setup_secrets.sh** - Secrets Manager
- **setup_iam.sh** - IAM roles
- **setup_ecs.sh** - ECS cluster and tasks
- **setup_alb.sh** - Load balancer
- **setup_services.sh** - ECS services
- **run_migrations.sh** - Database migrations
- **seed_data.sh** - Test data
- **deploy_frontend.sh** - Frontend deployment

### Utility Scripts
- **check_prerequisites.sh** - Verify prerequisites
- **update_cors.sh** - Update CORS after frontend
- **verify_deployment.sh** - Verify deployment

## Configuration

All configuration is saved to `aws_config.env` in this directory. This file contains:
- VPC and subnet IDs
- Security group IDs
- RDS and Redis endpoints
- ECR repository URIs
- Secret ARNs
- IAM role ARNs
- ALB DNS name
- CloudFront URL

## Deployment Time

Total deployment time: **~60-90 minutes**
- Infrastructure: ~15 minutes
- RDS/Redis: ~20 minutes
- ECR: ~10 minutes
- ECS: ~10 minutes
- Frontend: ~25 minutes
- Verification: ~5 minutes

## Cost

Estimated monthly cost: **~$110-140** (development/test setup)

## Troubleshooting

See individual script files for detailed error handling and troubleshooting.

## Support

Check CloudWatch logs if issues occur:
- API logs: `/ecs/tutor-scoring-api`
- Worker logs: `/ecs/tutor-scoring-worker`
