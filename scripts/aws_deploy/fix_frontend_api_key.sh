#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

export PATH="/opt/homebrew/bin:$PATH"
source aws_config.env 2>/dev/null || true
REGION="${AWS_REGION:-us-east-1}"
PROJECT_NAME="${PROJECT_NAME:-tutor-scoring}"

echo "🔧 Fixing Frontend API Key Configuration"
echo ""

# Get API key from Secrets Manager
echo "📥 Fetching API key from AWS Secrets Manager..."
API_KEY=$(aws secretsmanager get-secret-value \
  --secret-id ${PROJECT_NAME}/app-secrets \
  --region $REGION \
  --query 'SecretString' \
  --output text 2>/dev/null | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('API_KEY', ''))" 2>/dev/null)

if [ -z "$API_KEY" ]; then
  echo -e "${RED}❌ Error: Could not retrieve API key from Secrets Manager${NC}"
  echo "   Secret ID: ${PROJECT_NAME}/app-secrets"
  echo "   Region: $REGION"
  exit 1
fi

echo -e "${GREEN}✅ API key retrieved (length: ${#API_KEY})${NC}"

# Get ALB DNS for API URL
ALB_DNS="tutor-scoring-alb-2067881445.us-east-1.elb.amazonaws.com"
API_URL="http://${ALB_DNS}"

# Navigate to frontend directory
FRONTEND_DIR="../../frontend"
cd "$FRONTEND_DIR"

# Create .env.production with both URL and API key
echo "📝 Creating .env.production file..."
cat > .env.production <<EOF
VITE_API_URL=${API_URL}
VITE_API_KEY=${API_KEY}
EOF

echo -e "${GREEN}✅ Created .env.production with API key${NC}"

# Clean previous build
echo "🧹 Cleaning previous build..."
rm -rf dist node_modules/.vite

# Rebuild frontend with API key
echo "🔨 Rebuilding frontend with API key..."
npm run build

if [ $? -ne 0 ]; then
  echo -e "${RED}❌ Build failed${NC}"
  exit 1
fi

echo -e "${GREEN}✅ Frontend rebuilt successfully${NC}"

# Verify API key is in build (check for warning absence)
echo "🔍 Verifying API key in build..."
if grep -q "VITE_API_KEY not set" dist/assets/*.js 2>/dev/null; then
  echo -e "${YELLOW}⚠️  Warning: API key may not be in build${NC}"
else
  echo -e "${GREEN}✅ API key appears to be in build${NC}"
fi

# Deploy to S3
echo "📤 Deploying to S3..."
BUCKET_NAME="${PROJECT_NAME}-frontend"
aws s3 sync dist/ s3://${BUCKET_NAME} --delete --region $REGION

if [ $? -ne 0 ]; then
  echo -e "${RED}❌ S3 deployment failed${NC}"
  exit 1
fi

echo -e "${GREEN}✅ Deployed to S3${NC}"

# Invalidate CloudFront cache
echo "🔄 Invalidating CloudFront cache..."
DIST_ID=$(aws cloudfront list-distributions \
  --region $REGION \
  --query "DistributionList.Items[?contains(Comment, '${PROJECT_NAME}')].Id" \
  --output text | head -1)

if [ ! -z "$DIST_ID" ] && [ "$DIST_ID" != "None" ]; then
  INVALIDATION_ID=$(aws cloudfront create-invalidation \
    --distribution-id $DIST_ID \
    --paths "/*" \
    --region $REGION \
    --query 'Invalidation.Id' \
    --output text)
  
  echo -e "${GREEN}✅ CloudFront invalidation created: $INVALIDATION_ID${NC}"
else
  echo -e "${YELLOW}⚠️  Could not find CloudFront distribution${NC}"
fi

echo ""
echo -e "${GREEN}=== ✅ Frontend API Key Fix Complete ===${NC}"
echo ""
echo "Next steps:"
echo "  1. Wait 2-3 minutes for CloudFront cache to clear"
echo "  2. Hard refresh your browser (Cmd+Shift+R / Ctrl+Shift+R)"
echo "  3. Check browser console - should see '[API] API key configured'"
echo "  4. API calls should now work!"
echo ""
echo "Frontend URL: https://d2iu6aqgs7qt5d.cloudfront.net"
