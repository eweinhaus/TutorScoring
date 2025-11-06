#!/bin/bash
export PATH="/opt/homebrew/bin:$PATH"
set -e
source aws_config.env
REGION="${AWS_REGION:-us-east-1}"
PROJECT_NAME="${PROJECT_NAME:-tutor-scoring}"

echo "🔷 Updating AWS Deployment..."

# Step 1: Rebuild and push Docker images
echo ""
echo "🔷 [Step 1/3] Rebuilding and pushing Docker images..."
cd "$(dirname "$0")"
./setup_ecr.sh
source aws_config.env

# Step 2: Force ECS service updates
echo ""
echo "🔷 [Step 2/3] Forcing ECS service updates..."
echo "   Updating API service..."
aws ecs update-service \
    --cluster ${PROJECT_NAME}-cluster \
    --service ${PROJECT_NAME}-api-service \
    --force-new-deployment \
    --region $REGION > /dev/null

echo "   Updating Worker service..."
aws ecs update-service \
    --cluster ${PROJECT_NAME}-cluster \
    --service ${PROJECT_NAME}-worker-service \
    --force-new-deployment \
    --region $REGION > /dev/null

echo "⏳ Waiting for services to stabilize..."
aws ecs wait services-stable \
    --cluster ${PROJECT_NAME}-cluster \
    --services ${PROJECT_NAME}-api-service ${PROJECT_NAME}-worker-service \
    --region $REGION

echo "✅ Services updated and stable"

# Step 3: Rebuild and deploy frontend
echo ""
echo "🔷 [Step 3/3] Rebuilding and deploying frontend..."
./deploy_frontend.sh
source aws_config.env

echo ""
echo "✅ Deployment update complete!"
echo ""
if [ ! -z "$CLOUDFRONT_URL" ]; then
    echo "   Frontend URL: $CLOUDFRONT_URL"
fi
if [ ! -z "$ALB_DNS" ]; then
    echo "   API URL: http://$ALB_DNS/api/health"
fi

