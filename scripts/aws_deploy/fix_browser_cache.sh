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
    echo -e "${RED}❌ aws_config.env not found${NC}"
    exit 1
fi

REGION="${AWS_REGION:-us-east-1}"
PROJECT_NAME="${PROJECT_NAME:-tutor-scoring}"
BUCKET_NAME="${PROJECT_NAME}-frontend"

echo -e "${BLUE}🔧 Fixing Browser Cache Issues${NC}"
echo "===================================="
echo ""

# Update HTML file with no-cache headers
echo -e "${BLUE}[Step 1/3]${NC} Updating HTML cache headers..."
aws s3 cp s3://$BUCKET_NAME/index.html s3://$BUCKET_NAME/index.html \
    --cache-control "no-cache, no-store, must-revalidate" \
    --content-type "text/html" \
    --metadata-directive REPLACE \
    --region $REGION

echo -e "${GREEN}✅ HTML file updated with no-cache headers${NC}"

# Invalidate CloudFront cache again
echo ""
echo -e "${BLUE}[Step 2/3]${NC} Invalidating CloudFront cache..."

if [ -z "$CLOUDFRONT_URL" ]; then
    echo -e "${RED}❌ CLOUDFRONT_URL not set${NC}"
    exit 1
fi

DIST_ID=$(aws cloudfront list-distributions --region $REGION \
    --query "DistributionList.Items[?contains(DomainName, '${CLOUDFRONT_URL##https://}')].Id" \
    --output text 2>/dev/null | head -n1)

if [ -z "$DIST_ID" ] || [ "$DIST_ID" == "None" ]; then
    echo -e "${RED}❌ CloudFront distribution not found${NC}"
    exit 1
fi

INVALIDATION_ID=$(aws cloudfront create-invalidation \
    --distribution-id $DIST_ID \
    --paths "/*" \
    --region $REGION \
    --query 'Invalidation.Id' \
    --output text)

echo -e "${GREEN}✅ CloudFront cache invalidation created${NC}"
echo "   Invalidation ID: $INVALIDATION_ID"
echo -e "${YELLOW}⏳ Cache invalidation takes 2-3 minutes${NC}"

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           Cache Fix Complete!                        ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Next steps to clear Safari cache:"
echo ""
echo -e "${YELLOW}Option 1: Clear Safari Cache (Recommended)${NC}"
echo "  1. Open Safari"
echo "  2. Go to Safari > Settings (or Preferences)"
echo "  3. Click 'Advanced' tab"
echo "  4. Check 'Show Develop menu in menu bar'"
echo "  5. Go to Develop > Empty Caches (or Cmd+Option+E)"
echo "  6. Close and reopen Safari"
echo ""
echo -e "${YELLOW}Option 2: Hard Refresh${NC}"
echo "  1. Open the site: $CLOUDFRONT_URL"
echo "  2. Press Cmd+Option+R (hard refresh)"
echo "  3. Or hold Shift and click the refresh button"
echo ""
echo -e "${YELLOW}Option 3: Clear Website Data${NC}"
echo "  1. Safari > Settings > Privacy"
echo "  2. Click 'Manage Website Data...'"
echo "  3. Search for 'cloudfront.net' or 'd2iu6aqgs7qt5d'"
echo "  4. Select and click 'Remove'"
echo "  5. Reload the page"
echo ""
echo "Wait 2-3 minutes for CloudFront cache invalidation, then try again."

