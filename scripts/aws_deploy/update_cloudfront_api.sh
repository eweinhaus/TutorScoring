#!/bin/bash
export PATH="/opt/homebrew/bin:$PATH"
set -e
source aws_config.env
REGION="${AWS_REGION:-us-east-1}"
PROJECT_NAME="${PROJECT_NAME:-tutor-scoring}"

echo "🔷 Updating CloudFront to proxy /api/* to ALB..."

if [ -z "$CLOUDFRONT_URL" ] || [ -z "$ALB_DNS" ]; then
    echo "❌ Missing CLOUDFRONT_URL or ALB_DNS. Check aws_config.env"
    exit 1
fi

# Get distribution ID
DIST_ID=$(aws cloudfront list-distributions --region $REGION \
    --query "DistributionList.Items[?contains(DomainName, '${CLOUDFRONT_URL##https://}')].Id" \
    --output text 2>/dev/null | head -n1)

if [ -z "$DIST_ID" ] || [ "$DIST_ID" == "None" ]; then
    echo "❌ CloudFront distribution not found"
    exit 1
fi

echo "📋 Found distribution: $DIST_ID"

# Get current distribution config
echo "📥 Fetching current distribution config..."
aws cloudfront get-distribution-config \
    --id $DIST_ID \
    --region $REGION \
    > /tmp/cf-config.json

ETAG=$(jq -r '.ETag' /tmp/cf-config.json)
CONFIG=$(jq -r '.DistributionConfig' /tmp/cf-config.json)

# Check if ALB origin already exists
ALB_ORIGIN_ID="ALB-${PROJECT_NAME}"
ALB_ORIGIN_EXISTS=$(echo "$CONFIG" | jq -r ".Origins.Items[] | select(.Id == \"$ALB_ORIGIN_ID\") | .Id" 2>/dev/null || echo "")

if [ -z "$ALB_ORIGIN_EXISTS" ]; then
    echo "➕ Adding ALB origin..."
    # Add ALB origin with all required fields
    CONFIG=$(echo "$CONFIG" | jq \
        --arg ALB_ORIGIN_ID "$ALB_ORIGIN_ID" \
        --arg ALB_DNS "$ALB_DNS" \
        '.Origins.Items += [{
            "Id": $ALB_ORIGIN_ID,
            "DomainName": $ALB_DNS,
            "OriginPath": "",
            "CustomHeaders": {
                "Quantity": 0
            },
            "CustomOriginConfig": {
                "HTTPPort": 80,
                "HTTPSPort": 443,
                "OriginProtocolPolicy": "http-only",
                "OriginSslProtocols": {
                    "Quantity": 1,
                    "Items": ["TLSv1.2"]
                },
                "OriginReadTimeout": 30,
                "OriginKeepaliveTimeout": 5
            },
            "OriginShield": {
                "Enabled": false
            },
            "ConnectionAttempts": 3,
            "ConnectionTimeout": 10,
            "OriginAccessControlId": ""
        }] | .Origins.Quantity = (.Origins.Items | length)')
else
    echo "✅ ALB origin already exists"
fi

# Check if /api/* cache behavior exists
API_BEHAVIOR_EXISTS=$(echo "$CONFIG" | jq -r '.CacheBehaviors.Items[] | select(.PathPattern == "/api/*") | .PathPattern' 2>/dev/null || echo "")

if [ -z "$API_BEHAVIOR_EXISTS" ]; then
    echo "➕ Adding /api/* cache behavior..."
    # Add cache behavior for /api/*
    CONFIG=$(echo "$CONFIG" | jq \
        --arg ALB_ORIGIN_ID "$ALB_ORIGIN_ID" \
        --arg CLOUDFRONT_URL "$CLOUDFRONT_URL" \
        '.CacheBehaviors.Items += [{
            "PathPattern": "/api/*",
            "TargetOriginId": $ALB_ORIGIN_ID,
            "ViewerProtocolPolicy": "redirect-to-https",
            "AllowedMethods": {
                "Quantity": 7,
                "Items": ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"],
                "CachedMethods": {
                    "Quantity": 2,
                    "Items": ["GET", "HEAD"]
                }
            },
            "Compress": true,
            "ForwardedValues": {
                "QueryString": true,
                "Cookies": {
                    "Forward": "none"
                },
                "Headers": {
                    "Quantity": 3,
                    "Items": ["Host", "X-API-Key", "Authorization"]
                }
            },
            "MinTTL": 0,
            "DefaultTTL": 0,
            "MaxTTL": 0,
            "TrustedSigners": {
                "Enabled": false,
                "Quantity": 0
            }
        }] | .CacheBehaviors.Quantity = (.CacheBehaviors.Items | length)')
else
    echo "✅ /api/* cache behavior already exists"
fi

# Save updated config
echo "$CONFIG" > /tmp/cf-config-updated.json

# Update distribution
echo "🔄 Updating CloudFront distribution..."
aws cloudfront update-distribution \
    --id $DIST_ID \
    --distribution-config file:///tmp/cf-config-updated.json \
    --if-match "$ETAG" \
    --region $REGION \
    > /tmp/cf-update-response.json

echo "✅ CloudFront distribution update initiated"
echo "⏳ This may take 15-20 minutes to deploy"
echo ""
echo "📋 To check status:"
echo "   aws cloudfront get-distribution --id $DIST_ID --region $REGION --query 'Distribution.Status' --output text"

# Clean up
rm -f /tmp/cf-config.json /tmp/cf-config-updated.json /tmp/cf-update-response.json

