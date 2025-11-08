#!/bin/bash
export PATH="/opt/homebrew/bin:$PATH"
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Load configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -f aws_config.env ]; then
    source aws_config.env
else
    echo -e "${RED}❌ aws_config.env not found. Run setup scripts first.${NC}"
    exit 1
fi

REGION="${AWS_REGION:-us-east-1}"
PROJECT_NAME="${PROJECT_NAME:-tutor-scoring}"

echo -e "${BLUE}🔧 Fixing AWS Deployment Connection Issues${NC}"
echo "=============================================="
echo ""

# Verify required variables
if [ -z "$CLOUDFRONT_URL" ]; then
    echo -e "${RED}❌ CLOUDFRONT_URL not set in aws_config.env${NC}"
    exit 1
fi

if [ -z "$ALB_DNS" ]; then
    echo -e "${RED}❌ ALB_DNS not set in aws_config.env${NC}"
    exit 1
fi

if [ -z "$APP_SECRET_ARN" ]; then
    echo -e "${RED}❌ APP_SECRET_ARN not set in aws_config.env${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Configuration loaded${NC}"
echo "   CloudFront URL: $CLOUDFRONT_URL"
echo "   ALB DNS: $ALB_DNS"
echo ""

# Step 1: Verify/Update CloudFront API Proxy
echo -e "${BLUE}[Step 1/5]${NC} Verifying CloudFront API Proxy Configuration..."
DIST_ID=$(aws cloudfront list-distributions --region $REGION \
    --query "DistributionList.Items[?contains(DomainName, '${CLOUDFRONT_URL##https://}')].Id" \
    --output text 2>/dev/null | head -n1)

if [ -z "$DIST_ID" ] || [ "$DIST_ID" == "None" ]; then
    echo -e "${RED}❌ CloudFront distribution not found${NC}"
    exit 1
fi

echo "   Distribution ID: $DIST_ID"

# Get current config
aws cloudfront get-distribution-config \
    --id $DIST_ID \
    --region $REGION \
    > /tmp/cf-config.json

ETAG=$(jq -r '.ETag' /tmp/cf-config.json)
CONFIG=$(jq -r '.DistributionConfig' /tmp/cf-config.json)

# Check if /api/* cache behavior exists
API_BEHAVIOR_EXISTS=$(echo "$CONFIG" | jq -r '.CacheBehaviors.Items[]? | select(.PathPattern == "/api/*") | .PathPattern' 2>/dev/null || echo "")

if [ -z "$API_BEHAVIOR_EXISTS" ]; then
    echo -e "${YELLOW}⚠️  /api/* cache behavior not found. Running update_cloudfront_api.sh...${NC}"
    if [ -f update_cloudfront_api.sh ]; then
        ./update_cloudfront_api.sh
        echo -e "${GREEN}✅ CloudFront API proxy configured${NC}"
        echo -e "${YELLOW}⏳ Note: CloudFront updates take 15-20 minutes to deploy${NC}"
    else
        echo -e "${RED}❌ update_cloudfront_api.sh not found${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ /api/* cache behavior exists${NC}"
fi

# Step 2: Update Backend CORS Configuration
echo ""
echo -e "${BLUE}[Step 2/5]${NC} Updating Backend CORS Configuration..."

# Get current secrets
CURRENT_SECRETS=$(aws secretsmanager get-secret-value \
    --secret-id "$APP_SECRET_ARN" \
    --region $REGION \
    --query 'SecretString' \
    --output text)

# Check if CORS_ORIGINS is already set correctly
CURRENT_CORS=$(echo "$CURRENT_SECRETS" | jq -r '.CORS_ORIGINS // empty' 2>/dev/null || echo "")

if [ "$CURRENT_CORS" == "$CLOUDFRONT_URL" ]; then
    echo -e "${GREEN}✅ CORS_ORIGINS already set correctly: $CLOUDFRONT_URL${NC}"
else
    echo "   Updating CORS_ORIGINS to: $CLOUDFRONT_URL"
    
    # Update secrets with CORS_ORIGINS
    if command -v jq &> /dev/null; then
        UPDATED_SECRETS=$(echo "$CURRENT_SECRETS" | jq ". + {\"CORS_ORIGINS\": \"${CLOUDFRONT_URL}\"}")
    else
        # Fallback: simple JSON manipulation
        UPDATED_SECRETS=$(echo "$CURRENT_SECRETS" | sed 's/}$//')
        UPDATED_SECRETS="${UPDATED_SECRETS}, \"CORS_ORIGINS\": \"${CLOUDFRONT_URL}\"}"
    fi

    aws secretsmanager update-secret \
        --secret-id "$APP_SECRET_ARN" \
        --secret-string "$UPDATED_SECRETS" \
        --region $REGION > /dev/null

    echo -e "${GREEN}✅ Secrets updated with CORS_ORIGINS${NC}"
    
    # Update ECS task definition to include CORS_ORIGINS
    echo "   Updating ECS task definition..."
    
    CURRENT_TASK_DEF=$(aws ecs describe-task-definition \
        --task-definition ${PROJECT_NAME}-api \
        --region $REGION \
        --query 'taskDefinition' \
        --output json)
    
    # Check if CORS_ORIGINS is already in secrets references
    HAS_CORS_SECRET=$(echo "$CURRENT_TASK_DEF" | jq -r '.containerDefinitions[0].secrets[]? | select(.name == "CORS_ORIGINS") | .name' 2>/dev/null || echo "")
    
    if [ -z "$HAS_CORS_SECRET" ]; then
        # Add CORS_ORIGINS to secrets
        UPDATED_TASK_DEF=$(echo "$CURRENT_TASK_DEF" | jq \
            --arg APP_SECRET_ARN "$APP_SECRET_ARN" \
            '.containerDefinitions[0].secrets += [{
                "name": "CORS_ORIGINS",
                "valueFrom": ($APP_SECRET_ARN + ":CORS_ORIGINS::")
            }]')
        
        # Remove fields that can't be in new task definition
        UPDATED_TASK_DEF=$(echo "$UPDATED_TASK_DEF" | jq 'del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)')
        
        # Register new task definition
        NEW_TASK_DEF_REVISION=$(aws ecs register-task-definition \
            --cli-input-json "$UPDATED_TASK_DEF" \
            --region $REGION \
            --query 'taskDefinition.revision' \
            --output text)
        
        echo "   New task definition revision: $NEW_TASK_DEF_REVISION"
        
        # Update service
        aws ecs update-service \
            --cluster ${PROJECT_NAME}-cluster \
            --service ${PROJECT_NAME}-api-service \
            --task-definition ${PROJECT_NAME}-api:$NEW_TASK_DEF_REVISION \
            --region $REGION > /dev/null
        
        echo -e "${GREEN}✅ ECS service update initiated${NC}"
        echo -e "${YELLOW}⏳ Waiting for service to stabilize (this may take a few minutes)...${NC}"
        
        aws ecs wait services-stable \
            --cluster ${PROJECT_NAME}-cluster \
            --services ${PROJECT_NAME}-api-service \
            --region $REGION
        
        echo -e "${GREEN}✅ Service updated and stable${NC}"
    else
        echo -e "${GREEN}✅ CORS_ORIGINS already in task definition${NC}"
    fi
fi

# Step 3: Rebuild Frontend with Relative URLs
echo ""
echo -e "${BLUE}[Step 3/5]${NC} Rebuilding Frontend with Correct Configuration..."

cd ../../frontend

# Get API key from Secrets Manager
API_KEY=$(aws secretsmanager get-secret-value \
    --secret-id "$APP_SECRET_ARN" \
    --region $REGION \
    --query 'SecretString' \
    --output text 2>/dev/null | jq -r '.API_KEY // empty' 2>/dev/null || echo "")

if [ -z "$API_KEY" ]; then
    echo -e "${YELLOW}⚠️  Warning: API_KEY not found in Secrets Manager${NC}"
    echo "   API requests will fail without authentication"
fi

# Create .env.production with API key but NO VITE_API_URL (use relative URLs)
if [ -n "$API_KEY" ]; then
    echo "VITE_API_KEY=${API_KEY}" > .env.production
    echo "# VITE_API_URL is intentionally not set - using relative URLs for CloudFront" >> .env.production
    echo -e "${GREEN}✅ Created .env.production with API key (relative URLs)${NC}"
else
    touch .env.production
    echo -e "${YELLOW}⚠️  Building without API key${NC}"
fi

# Clean previous build
echo "   Cleaning previous build..."
rm -rf dist node_modules/.vite

# Rebuild
echo "   Building frontend..."
npm run build

# Clean up .env.production
rm -f .env.production
echo -e "${GREEN}✅ Frontend rebuilt${NC}"

# Step 4: Deploy to S3
echo ""
echo -e "${BLUE}[Step 4/5]${NC} Deploying Frontend to S3..."

BUCKET_NAME="${PROJECT_NAME}-frontend"
aws s3 sync dist/ s3://$BUCKET_NAME --delete --region $REGION

echo -e "${GREEN}✅ Frontend deployed to S3${NC}"

# Step 5: Invalidate CloudFront Cache
echo ""
echo -e "${BLUE}[Step 5/5]${NC} Invalidating CloudFront Cache..."

INVALIDATION_ID=$(aws cloudfront create-invalidation \
    --distribution-id $DIST_ID \
    --paths "/*" \
    --region $REGION \
    --query 'Invalidation.Id' \
    --output text)

echo -e "${GREEN}✅ CloudFront cache invalidation created${NC}"
echo "   Invalidation ID: $INVALIDATION_ID"
echo -e "${YELLOW}⏳ Cache invalidation takes 2-3 minutes${NC}"

# Clean up
rm -f /tmp/cf-config.json

# Summary
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           Fix Complete!                                ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Summary of changes:"
echo "  ✅ CloudFront API proxy verified/configured"
echo "  ✅ Backend CORS updated to allow: $CLOUDFRONT_URL"
echo "  ✅ Frontend rebuilt with relative URLs"
echo "  ✅ Frontend deployed to S3"
echo "  ✅ CloudFront cache invalidated"
echo ""
echo "Next steps:"
echo "  1. Wait 2-3 minutes for cache invalidation"
echo "  2. Wait 15-20 minutes if CloudFront was updated"
echo "  3. Test the application at: $CLOUDFRONT_URL"
echo "  4. Clear browser cache if issues persist"
echo ""
echo "To verify deployment:"
echo "  cd scripts/aws_deploy && ./verify_deployment.sh"

