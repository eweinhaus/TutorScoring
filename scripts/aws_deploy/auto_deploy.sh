#!/bin/bash
export PATH="/opt/homebrew/bin:$PATH"
# Fully Automated AWS Deployment Script
# This script handles the complete deployment with minimal manual intervention

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Automated AWS Deployment - TutorScoring System     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Step 0: Check Prerequisites
echo -e "${BLUE}[Step 0/12]${NC} Checking Prerequisites..."
if ! ./check_prerequisites.sh; then
    echo -e "${RED}❌ Prerequisites check failed${NC}"
    exit 1
fi
echo ""

# Set region
export AWS_REGION="${AWS_REGION:-us-east-1}"
echo -e "${GREEN}✅ Using AWS Region: $AWS_REGION${NC}"
echo ""

# Load existing config if available
if [ -f aws_config.env ]; then
    echo -e "${YELLOW}📋 Found existing configuration${NC}"
    source aws_config.env
    read -p "Continue with existing config? (y/n): " CONTINUE
    if [ "$CONTINUE" != "y" ]; then
        echo "Aborted"
        exit 0
    fi
    echo ""
fi

# Set admin email (default)
export ADMIN_EMAIL="${ADMIN_EMAIL:-etweinhaus@gmail.com}"

# Generate API_KEY and SECRET_KEY if not set
if [ -z "$API_KEY" ]; then
    API_KEY=$(openssl rand -hex 32)
    export API_KEY
    echo -e "${GREEN}✅ Generated API Key${NC}"
fi

if [ -z "$SECRET_KEY" ]; then
    SECRET_KEY=$(openssl rand -hex 32)
    export SECRET_KEY
    echo -e "${GREEN}✅ Generated Secret Key${NC}"
fi

# SendGrid API key - prompt only when needed (as late as possible)
# Will be prompted in setup_secrets.sh

# Step 1: Infrastructure
echo -e "${BLUE}[Step 1/12]${NC} Setting up Infrastructure (VPC, Subnets, Security Groups)..."
if [ -f setup_infrastructure.sh ]; then
    ./setup_infrastructure.sh
    source aws_config.env
else
    echo -e "${RED}❌ setup_infrastructure.sh not found${NC}"
    exit 1
fi
echo ""

# Step 2: RDS and Redis
echo -e "${BLUE}[Step 2/12]${NC} Setting up RDS and ElastiCache (this takes 15-20 minutes)..."
if [ -f setup_rds_redis.sh ]; then
    ./setup_rds_redis.sh
    source aws_config.env
else
    echo -e "${RED}❌ setup_rds_redis.sh not found${NC}"
    exit 1
fi
echo ""

# Step 3: ECR
echo -e "${BLUE}[Step 3/12]${NC} Setting up ECR and pushing Docker images..."
if [ -f setup_ecr.sh ]; then
    ./setup_ecr.sh
    source aws_config.env
else
    echo -e "${RED}❌ setup_ecr.sh not found${NC}"
    exit 1
fi
echo ""

# Step 4: Secrets
echo -e "${BLUE}[Step 4/12]${NC} Setting up Secrets Manager..."
echo -e "${YELLOW}📝 SendGrid API Key will be prompted now (or press Enter to skip)${NC}"
if [ -f setup_secrets.sh ]; then
    ./setup_secrets.sh
    source aws_config.env
else
    echo -e "${RED}❌ setup_secrets.sh not found${NC}"
    exit 1
fi
echo ""

# Step 5: IAM
echo -e "${BLUE}[Step 5/12]${NC} Setting up IAM Roles..."
if [ -f setup_iam.sh ]; then
    ./setup_iam.sh
    source aws_config.env
else
    echo -e "${RED}❌ setup_iam.sh not found${NC}"
    exit 1
fi
echo ""

# Step 6: ECS
echo -e "${BLUE}[Step 6/12]${NC} Setting up ECS Cluster and Task Definitions..."
if [ -f setup_ecs.sh ]; then
    ./setup_ecs.sh
    source aws_config.env
else
    echo -e "${RED}❌ setup_ecs.sh not found${NC}"
    exit 1
fi
echo ""

# Step 7: ALB
echo -e "${BLUE}[Step 7/12]${NC} Setting up Application Load Balancer..."
if [ -f setup_alb.sh ]; then
    ./setup_alb.sh
    source aws_config.env
else
    echo -e "${RED}❌ setup_alb.sh not found${NC}"
    exit 1
fi
echo ""

# Step 8: Services
echo -e "${BLUE}[Step 8/12]${NC} Creating ECS Services..."
if [ -f setup_services.sh ]; then
    ./setup_services.sh
    source aws_config.env
else
    echo -e "${RED}❌ setup_services.sh not found${NC}"
    exit 1
fi
echo ""

# Step 9: Migrations
echo -e "${BLUE}[Step 9/12]${NC} Running Database Migrations..."
if [ -f run_migrations.sh ]; then
    # Use ECS task option automatically
    echo "2" | ./run_migrations.sh
    source aws_config.env
else
    echo -e "${RED}❌ run_migrations.sh not found${NC}"
    exit 1
fi
echo ""

# Step 10: Seed Data
echo -e "${BLUE}[Step 10/12]${NC} Seeding Test Data..."
if [ -f seed_data.sh ]; then
    # Use ECS task option automatically
    echo "2" | ./seed_data.sh
    source aws_config.env
else
    echo -e "${RED}❌ seed_data.sh not found${NC}"
    exit 1
fi
echo ""

# Step 11: Frontend
echo -e "${BLUE}[Step 11/12]${NC} Deploying Frontend (this takes 20-25 minutes)..."
if [ -f deploy_frontend.sh ]; then
    ./deploy_frontend.sh
    source aws_config.env
else
    echo -e "${RED}❌ deploy_frontend.sh not found${NC}"
    exit 1
fi
echo ""

# Step 12: Update CORS
echo -e "${BLUE}[Step 12/12]${NC} Updating CORS Configuration..."
if [ -f update_cors.sh ]; then
    ./update_cors.sh
    source aws_config.env
else
    echo -e "${YELLOW}⚠️  update_cors.sh not found - skipping CORS update${NC}"
    echo -e "${YELLOW}   You may need to update CORS manually${NC}"
fi
echo ""

# Verification
echo -e "${BLUE}[Verification]${NC} Verifying Deployment..."
if [ -f verify_deployment.sh ]; then
    ./verify_deployment.sh
else
    echo -e "${YELLOW}⚠️  verify_deployment.sh not found - skipping verification${NC}"
fi
echo ""

# Summary
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           Deployment Complete!                        ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}📋 Deployment Summary:${NC}"
echo ""
if [ ! -z "$ALB_DNS" ]; then
    echo -e "   ${GREEN}API URL:${NC} http://$ALB_DNS"
    echo -e "   ${GREEN}Health Check:${NC} http://$ALB_DNS/api/health"
fi
if [ ! -z "$CLOUDFRONT_URL" ]; then
    echo -e "   ${GREEN}Frontend URL:${NC} $CLOUDFRONT_URL"
fi
echo ""
if [ ! -z "$API_KEY" ]; then
    echo -e "   ${YELLOW}API Key:${NC} $API_KEY"
    echo -e "   ${YELLOW}(Save this securely!)${NC}"
fi
echo ""
echo -e "${BLUE}📝 Configuration saved to:${NC} aws_config.env"
echo ""
echo -e "${GREEN}✅ All deployment steps completed!${NC}"

