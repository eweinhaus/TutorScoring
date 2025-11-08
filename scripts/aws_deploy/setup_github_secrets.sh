#!/bin/bash
# Script to help set up GitHub Secrets for CI/CD deployment
# This script extracts values from aws_config.env and provides instructions

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
echo -e "${BLUE}║   GitHub Secrets Setup Helper                        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

if [ ! -f "aws_config.env" ]; then
    echo -e "${RED}❌ Error: aws_config.env not found${NC}"
    echo "   Please run the deployment setup first to generate aws_config.env"
    exit 1
fi

source aws_config.env

echo -e "${YELLOW}📋 Required GitHub Secrets:${NC}"
echo ""
echo "Go to: https://github.com/YOUR_USERNAME/YOUR_REPO/settings/secrets/actions"
echo ""
echo "Add the following secrets:"
echo ""

# Required secrets
declare -a secrets=(
    "AWS_ACCESS_KEY_ID"
    "AWS_SECRET_ACCESS_KEY"
    "AWS_VPC_ID"
    "AWS_PUB_SUBNET_1"
    "AWS_PUB_SUBNET_2"
    "AWS_PRIV_SUBNET_1"
    "AWS_PRIV_SUBNET_2"
    "AWS_ALB_SG"
    "AWS_API_SG"
    "AWS_WORKER_SG"
    "AWS_DB_SG"
    "AWS_REDIS_SG"
    "AWS_API_REPO_URI"
    "AWS_WORKER_REPO_URI"
    "AWS_EXEC_ROLE_ARN"
    "AWS_TASK_ROLE_ARN"
    "AWS_DB_ENDPOINT"
    "AWS_REDIS_ENDPOINT"
    "AWS_DB_SECRET_ARN"
    "AWS_REDIS_SECRET_ARN"
    "AWS_APP_SECRET_ARN"
    "AWS_ALB_DNS"
    "AWS_CLOUDFRONT_URL"
)

echo -e "${GREEN}=== Secret Values ===${NC}"
echo ""

# AWS credentials (need to be set manually)
echo -e "${YELLOW}AWS_ACCESS_KEY_ID${NC}"
echo "   (Set this manually from your AWS IAM user)"
echo ""

echo -e "${YELLOW}AWS_SECRET_ACCESS_KEY${NC}"
echo "   (Set this manually from your AWS IAM user)"
echo ""

# Extract from aws_config.env
for secret in "${secrets[@]}"; do
    case $secret in
        AWS_ACCESS_KEY_ID|AWS_SECRET_ACCESS_KEY)
            continue
            ;;
        AWS_VPC_ID)
            value=$VPC_ID
            ;;
        AWS_PUB_SUBNET_1)
            value=$PUB_SUBNET_1
            ;;
        AWS_PUB_SUBNET_2)
            value=$PUB_SUBNET_2
            ;;
        AWS_PRIV_SUBNET_1)
            value=$PRIV_SUBNET_1
            ;;
        AWS_PRIV_SUBNET_2)
            value=$PRIV_SUBNET_2
            ;;
        AWS_ALB_SG)
            value=$ALB_SG
            ;;
        AWS_API_SG)
            value=$API_SG
            ;;
        AWS_WORKER_SG)
            value=$WORKER_SG
            ;;
        AWS_DB_SG)
            value=$DB_SG
            ;;
        AWS_REDIS_SG)
            value=$REDIS_SG
            ;;
        AWS_API_REPO_URI)
            value=$API_REPO_URI
            ;;
        AWS_WORKER_REPO_URI)
            value=$WORKER_REPO_URI
            ;;
        AWS_EXEC_ROLE_ARN)
            value=$EXEC_ROLE_ARN
            ;;
        AWS_TASK_ROLE_ARN)
            value=$TASK_ROLE_ARN
            ;;
        AWS_DB_ENDPOINT)
            value=$DB_ENDPOINT
            ;;
        AWS_REDIS_ENDPOINT)
            value=$REDIS_ENDPOINT
            ;;
        AWS_DB_SECRET_ARN)
            value=$DB_SECRET_ARN
            ;;
        AWS_REDIS_SECRET_ARN)
            value=$REDIS_SECRET_ARN
            ;;
        AWS_APP_SECRET_ARN)
            value=$APP_SECRET_ARN
            ;;
        AWS_ALB_DNS)
            value=$ALB_DNS
            ;;
        AWS_CLOUDFRONT_URL)
            value=$CLOUDFRONT_URL
            ;;
    esac

    if [ ! -z "$value" ]; then
        echo -e "${GREEN}$secret${NC}"
        echo "   $value"
        echo ""
    else
        echo -e "${RED}$secret${NC} (⚠️  NOT FOUND in aws_config.env)"
        echo ""
    fi
done

echo ""
echo -e "${BLUE}📝 Quick Setup Instructions:${NC}"
echo ""
echo "1. Create an IAM user with deployment permissions:"
echo "   - ECR: Push/Pull images"
echo "   - ECS: Update services"
echo "   - S3: Upload frontend files"
echo "   - CloudFront: Create invalidations"
echo "   - Secrets Manager: Read secrets (for API key)"
echo ""
echo "2. Get the Access Key ID and Secret Access Key from the IAM user"
echo ""
echo "3. Add all secrets to GitHub:"
echo "   Settings → Secrets and variables → Actions → New repository secret"
echo ""
echo "4. The workflow will automatically run on pushes to main branch"
echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"

