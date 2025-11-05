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

echo "🔍 Checking Frontend Configuration"
echo ""

# Check if .env.production exists
FRONTEND_DIR="../../frontend"
if [ -f "$FRONTEND_DIR/.env.production" ]; then
  echo -e "${GREEN}✅ .env.production file exists${NC}"
  echo "   Contents:"
  cat "$FRONTEND_DIR/.env.production" | sed 's/\(.*=.*\)/   \1/'
else
  echo -e "${RED}❌ .env.production file not found${NC}"
fi

echo ""

# Check API key in Secrets Manager
echo "📥 Checking API key in AWS Secrets Manager..."
API_KEY=$(aws secretsmanager get-secret-value \
  --secret-id ${PROJECT_NAME}/app-secrets \
  --region $REGION \
  --query 'SecretString' \
  --output text 2>/dev/null | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('API_KEY', ''))" 2>/dev/null)

if [ -z "$API_KEY" ]; then
  echo -e "${RED}❌ API key not found in Secrets Manager${NC}"
else
  echo -e "${GREEN}✅ API key found in Secrets Manager${NC}"
  echo "   Length: ${#API_KEY} characters"
  echo "   First 20 chars: ${API_KEY:0:20}..."
fi

echo ""

# Check built frontend
if [ -d "$FRONTEND_DIR/dist" ]; then
  echo "📦 Checking built frontend..."
  
  # Check for API key warning in built files
  if grep -q "VITE_API_KEY not set" "$FRONTEND_DIR/dist/assets"/*.js 2>/dev/null; then
    echo -e "${RED}❌ API key warning found in build${NC}"
    echo "   This means the frontend was built without VITE_API_KEY"
  else
    echo -e "${GREEN}✅ No API key warning in build${NC}"
  fi
  
  # Check for hardcoded URLs
  if grep -q "tutor-scoring-alb" "$FRONTEND_DIR/dist/assets"/*.js 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Hardcoded ALB URLs found in build${NC}"
  else
    echo -e "${GREEN}✅ No hardcoded URLs found (using relative URLs)${NC}"
  fi
else
  echo -e "${YELLOW}⚠️  Frontend not built (dist/ directory not found)${NC}"
fi

echo ""
echo "💡 To fix API key issue, run:"
echo "   ./fix_frontend_api_key.sh"
