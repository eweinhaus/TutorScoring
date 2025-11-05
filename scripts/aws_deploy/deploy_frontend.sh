#!/bin/bash
export PATH="/opt/homebrew/bin:$PATH"
set -e
source aws_config.env
REGION="${AWS_REGION:-us-east-1}"
PROJECT_NAME="${PROJECT_NAME:-tutor-scoring}"
BUCKET_NAME="${PROJECT_NAME}-frontend"

echo "🔷 Deploying Frontend..."

if [ -z "$ALB_DNS" ]; then
    echo "❌ ALB DNS not set. Run setup_alb.sh first."
    exit 1
fi

# Build frontend
cd ../../frontend
echo "VITE_API_URL=http://${ALB_DNS}" > .env.production

if [ ! -d "node_modules" ]; then
    npm install
fi

npm run build

# Create S3 bucket
if ! aws s3api head-bucket --bucket $BUCKET_NAME --region $REGION 2>/dev/null; then
    if [ "$REGION" == "us-east-1" ]; then
        aws s3api create-bucket --bucket $BUCKET_NAME --region $REGION
    else
        aws s3api create-bucket --bucket $BUCKET_NAME --region $REGION --create-bucket-configuration LocationConstraint=$REGION
    fi
fi

# Upload files
aws s3 sync dist/ s3://$BUCKET_NAME --delete --region $REGION

# Create CloudFront distribution
EXISTING_DIST=$(aws cloudfront list-distributions --region $REGION --query "DistributionList.Items[?contains(Origins.Items[0].DomainName, '${BUCKET_NAME}.s3')].Id" --output text 2>/dev/null | head -n1)

if [ -z "$EXISTING_DIST" ] || [ "$EXISTING_DIST" == "None" ]; then
    # Get or create OAC
    OAC_ID=$(aws cloudfront list-origin-access-controls --region $REGION --query "OriginAccessControlList.Items[?Name=='${PROJECT_NAME}-oac'].Id" --output text 2>/dev/null)
    if [ -z "$OAC_ID" ] || [ "$OAC_ID" == "None" ]; then
        OAC_ID=$(aws cloudfront create-origin-access-control \
            --origin-access-control-config "Name=${PROJECT_NAME}-oac,OriginAccessControlOriginType=s3,SigningBehavior=always,SigningProtocol=sigv4" \
            --region $REGION --query 'OriginAccessControl.Id' --output text)
    fi
    
    # Create distribution config
    DIST_CONFIG=$(cat <<EOF
{
    "CallerReference": "${PROJECT_NAME}-$(date +%s)",
    "Comment": "${PROJECT_NAME}",
    "DefaultRootObject": "index.html",
    "Origins": {
        "Quantity": 1,
        "Items": [{
            "Id": "S3-${BUCKET_NAME}",
            "DomainName": "${BUCKET_NAME}.s3.${REGION}.amazonaws.com",
            "S3OriginConfig": {
                "OriginAccessIdentity": ""
            },
            "OriginAccessControlId": "${OAC_ID}"
        }]
    },
    "DefaultCacheBehavior": {
        "TargetOriginId": "S3-${BUCKET_NAME}",
        "ViewerProtocolPolicy": "redirect-to-https",
        "AllowedMethods": {"Quantity": 3, "Items": ["GET","HEAD","OPTIONS"]},
        "Compress": true,
        "ForwardedValues": {"QueryString": false, "Cookies": {"Forward": "none"}},
        "MinTTL": 0
    },
    "CustomErrorResponses": {
        "Quantity": 2,
        "Items": [
            {"ErrorCode": 403, "ResponsePagePath": "/index.html", "ResponseCode": "200"},
            {"ErrorCode": 404, "ResponsePagePath": "/index.html", "ResponseCode": "200"}
        ]
    },
    "Enabled": true
}
EOF
)
    
    DIST_ID=$(echo "$DIST_CONFIG" | aws cloudfront create-distribution --region $REGION --distribution-config file:///dev/stdin --query 'Distribution.Id' --output text)
    CLOUDFRONT_DOMAIN=$(aws cloudfront get-distribution --id $DIST_ID --region $REGION --query 'Distribution.DomainName' --output text)
    
    echo "⏳ CloudFront deploying (15-20 minutes)..."
else
    DIST_ID=$EXISTING_DIST
    CLOUDFRONT_DOMAIN=$(aws cloudfront get-distribution --id $DIST_ID --region $REGION --query 'Distribution.DomainName' --output text)
fi

CLOUDFRONT_URL="https://${CLOUDFRONT_DOMAIN}"

# Update bucket policy
aws s3api put-bucket-policy --bucket $BUCKET_NAME --policy "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":\"*\",\"Action\":\"s3:GetObject\",\"Resource\":\"arn:aws:s3:::${BUCKET_NAME}/*\"}]}" --region $REGION

# Save to config
cat >> aws_config.env << EOF
export CLOUDFRONT_DOMAIN=$CLOUDFRONT_DOMAIN
export CLOUDFRONT_URL=$CLOUDFRONT_URL
EOF

cd ../scripts/aws_deploy

echo "✅ Frontend deployed: $CLOUDFRONT_URL"
