#!/bin/bash
export PATH="/opt/homebrew/bin:$PATH"
# Deployment Verification Script

set -e

# Load configuration
if [ -f aws_config.env ]; then
    source aws_config.env
fi

REGION="${AWS_REGION:-us-east-1}"
PROJECT_NAME="${PROJECT_NAME:-tutor-scoring}"

echo "🔍 Verifying AWS Deployment"
echo "=========================="
echo ""

ERRORS=0
WARNINGS=0

# Check VPC
echo "📋 Checking VPC..."
if [ ! -z "$VPC_ID" ]; then
    VPC_STATUS=$(aws ec2 describe-vpcs --vpc-ids $VPC_ID --region $REGION --query 'Vpcs[0].State' --output text 2>/dev/null)
    if [ "$VPC_STATUS" == "available" ]; then
        echo "✅ VPC: $VPC_ID (available)"
    else
        echo "❌ VPC: $VPC_ID (status: $VPC_STATUS)"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "⚠️  VPC_ID not set"
    WARNINGS=$((WARNINGS + 1))
fi

# Check RDS
echo ""
echo "📋 Checking RDS..."
if [ ! -z "$DB_ENDPOINT" ]; then
    DB_STATUS=$(aws rds describe-db-instances --db-instance-identifier ${PROJECT_NAME}-db --region $REGION --query 'DBInstances[0].DBInstanceStatus' --output text 2>/dev/null)
    if [ "$DB_STATUS" == "available" ]; then
        echo "✅ RDS: $DB_ENDPOINT (available)"
    else
        echo "⚠️  RDS: $DB_ENDPOINT (status: $DB_STATUS)"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo "⚠️  DB_ENDPOINT not set"
    WARNINGS=$((WARNINGS + 1))
fi

# Check Redis
echo ""
echo "📋 Checking Redis..."
if [ ! -z "$REDIS_ENDPOINT" ]; then
    REDIS_STATUS=$(aws elasticache describe-cache-clusters --cache-cluster-id ${PROJECT_NAME}-redis --region $REGION --query 'CacheClusters[0].CacheClusterStatus' --output text 2>/dev/null)
    if [ "$REDIS_STATUS" == "available" ]; then
        echo "✅ Redis: $REDIS_ENDPOINT (available)"
    else
        echo "⚠️  Redis: $REDIS_ENDPOINT (status: $REDIS_STATUS)"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo "⚠️  REDIS_ENDPOINT not set"
    WARNINGS=$((WARNINGS + 1))
fi

# Check ECS Services
echo ""
echo "📋 Checking ECS Services..."
API_SERVICE_STATUS=$(aws ecs describe-services --cluster ${PROJECT_NAME}-cluster --services ${PROJECT_NAME}-api-service --region $REGION --query 'services[0].status' --output text 2>/dev/null)
if [ "$API_SERVICE_STATUS" == "ACTIVE" ]; then
    API_RUNNING=$(aws ecs describe-services --cluster ${PROJECT_NAME}-cluster --services ${PROJECT_NAME}-api-service --region $REGION --query 'services[0].runningCount' --output text)
    echo "✅ API Service: ACTIVE (running: $API_RUNNING)"
else
    echo "❌ API Service: $API_SERVICE_STATUS"
    ERRORS=$((ERRORS + 1))
fi

WORKER_SERVICE_STATUS=$(aws ecs describe-services --cluster ${PROJECT_NAME}-cluster --services ${PROJECT_NAME}-worker-service --region $REGION --query 'services[0].status' --output text 2>/dev/null)
if [ "$WORKER_SERVICE_STATUS" == "ACTIVE" ]; then
    WORKER_RUNNING=$(aws ecs describe-services --cluster ${PROJECT_NAME}-cluster --services ${PROJECT_NAME}-worker-service --region $REGION --query 'services[0].runningCount' --output text)
    echo "✅ Worker Service: ACTIVE (running: $WORKER_RUNNING)"
else
    echo "❌ Worker Service: $WORKER_SERVICE_STATUS"
    ERRORS=$((ERRORS + 1))
fi

# Check ALB
echo ""
echo "📋 Checking Application Load Balancer..."
if [ ! -z "$ALB_DNS" ]; then
    ALB_STATE=$(aws elbv2 describe-load-balancers --names ${PROJECT_NAME}-alb --region $REGION --query 'LoadBalancers[0].State.Code' --output text 2>/dev/null)
    if [ "$ALB_STATE" == "active" ]; then
        echo "✅ ALB: $ALB_DNS (active)"
        
        # Test health endpoint
        echo ""
        echo "🔷 Testing API health endpoint..."
        HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" http://${ALB_DNS}/api/health 2>/dev/null || echo -e "\n000")
        HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n1)
        RESPONSE_BODY=$(echo "$HEALTH_RESPONSE" | head -n-1)
        
        if [ "$HTTP_CODE" == "200" ]; then
            echo "✅ Health endpoint: HTTP $HTTP_CODE"
            echo "   Response: $RESPONSE_BODY"
        else
            echo "⚠️  Health endpoint: HTTP $HTTP_CODE"
            WARNINGS=$((WARNINGS + 1))
        fi
    else
        echo "⚠️  ALB: $ALB_DNS (state: $ALB_STATE)"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo "⚠️  ALB_DNS not set"
    WARNINGS=$((WARNINGS + 1))
fi

# Check CloudFront
echo ""
echo "📋 Checking CloudFront..."
if [ ! -z "$CLOUDFRONT_DOMAIN" ]; then
    CF_STATUS=$(aws cloudfront get-distribution --id $(aws cloudfront list-distributions --region $REGION --query "DistributionList.Items[?contains(DomainName, '${CLOUDFRONT_DOMAIN}')].Id" --output text) --region $REGION --query 'Distribution.Status' --output text 2>/dev/null)
    if [ "$CF_STATUS" == "Deployed" ]; then
        echo "✅ CloudFront: $CLOUDFRONT_DOMAIN (deployed)"
    else
        echo "⚠️  CloudFront: $CLOUDFRONT_DOMAIN (status: $CF_STATUS)"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo "⚠️  CLOUDFRONT_DOMAIN not set (frontend may not be deployed yet)"
    WARNINGS=$((WARNINGS + 1))
fi

# Summary
echo ""
echo "=========================="
echo "Verification Summary"
echo "=========================="
echo "Errors: $ERRORS"
echo "Warnings: $WARNINGS"
echo ""

if [ $ERRORS -gt 0 ]; then
    echo "❌ Deployment has errors. Please review and fix."
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo "⚠️  Deployment has warnings but is functional."
    exit 0
else
    echo "✅ Deployment verification passed!"
    exit 0
fi

