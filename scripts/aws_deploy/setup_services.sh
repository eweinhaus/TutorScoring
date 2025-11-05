#!/bin/bash
export PATH="/opt/homebrew/bin:$PATH"
set -e
source aws_config.env
REGION="${AWS_REGION:-us-east-1}"
PROJECT_NAME="${PROJECT_NAME:-tutor-scoring}"

echo "🔷 Creating ECS Services..."

if [ -z "$VPC_ID" ] || [ -z "$PRIV_SUBNET_1" ] || [ -z "$TG_ARN" ]; then
    echo "❌ Missing configuration. Run previous scripts first."
    exit 1
fi

# Create API service
if ! aws ecs describe-services --cluster ${PROJECT_NAME}-cluster --services ${PROJECT_NAME}-api-service --region $REGION --query 'services[0].status' --output text 2>/dev/null | grep -q ACTIVE; then
    aws ecs create-service \
        --cluster ${PROJECT_NAME}-cluster \
        --service-name ${PROJECT_NAME}-api-service \
        --task-definition ${PROJECT_NAME}-api \
        --desired-count 1 \
        --launch-type FARGATE \
        --network-configuration "awsvpcConfiguration={subnets=[${PRIV_SUBNET_1},${PRIV_SUBNET_2}],securityGroups=[${API_SG}],assignPublicIp=ENABLED}" \
        --load-balancers "targetGroupArn=${TG_ARN},containerName=api,containerPort=8000" \
        --health-check-grace-period-seconds 60 \
        --region $REGION >/dev/null
    
    echo "⏳ Waiting for API service to stabilize..."
    aws ecs wait services-stable --cluster ${PROJECT_NAME}-cluster --services ${PROJECT_NAME}-api-service --region $REGION
fi

# Create worker service
if ! aws ecs describe-services --cluster ${PROJECT_NAME}-cluster --services ${PROJECT_NAME}-worker-service --region $REGION --query 'services[0].status' --output text 2>/dev/null | grep -q ACTIVE; then
    aws ecs create-service \
        --cluster ${PROJECT_NAME}-cluster \
        --service-name ${PROJECT_NAME}-worker-service \
        --task-definition ${PROJECT_NAME}-worker \
        --desired-count 1 \
        --launch-type FARGATE \
        --network-configuration "awsvpcConfiguration={subnets=[${PRIV_SUBNET_1},${PRIV_SUBNET_2}],securityGroups=[${WORKER_SG}],assignPublicIp=ENABLED}" \
        --region $REGION >/dev/null
    
    echo "⏳ Waiting for worker service to stabilize..."
    aws ecs wait services-stable --cluster ${PROJECT_NAME}-cluster --services ${PROJECT_NAME}-worker-service --region $REGION
fi

echo "✅ Services created"
echo "   API: http://${ALB_DNS}/api/health"
