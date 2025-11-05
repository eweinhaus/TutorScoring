#!/bin/bash
export PATH="/opt/homebrew/bin:$PATH"
set -e
source aws_config.env
REGION="${AWS_REGION:-us-east-1}"
PROJECT_NAME="${PROJECT_NAME:-tutor-scoring}"

echo "🔷 Seeding Test Data via ECS Task..."

if [ -z "$PRIV_SUBNET_1" ] || [ -z "$API_SG" ]; then
    echo "❌ Missing configuration."
    exit 1
fi

TASK_ARN=$(aws ecs run-task \
    --cluster ${PROJECT_NAME}-cluster \
    --task-definition ${PROJECT_NAME}-api \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[${PRIV_SUBNET_1},${PRIV_SUBNET_2}],securityGroups=[${API_SG}],assignPublicIp=ENABLED}" \
    --overrides '{"containerOverrides":[{"name":"api","command":["python","scripts/generate_data.py"]}]}' \
    --region $REGION \
    --query 'tasks[0].taskArn' --output text)

echo "⏳ Task started: $TASK_ARN"
echo "⏳ This may take several minutes..."

aws ecs wait tasks-stopped --cluster ${PROJECT_NAME}-cluster --tasks $TASK_ARN --region $REGION

EXIT_CODE=$(aws ecs describe-tasks --cluster ${PROJECT_NAME}-cluster --tasks $TASK_ARN --region $REGION --query 'tasks[0].containers[0].exitCode' --output text)

if [ "$EXIT_CODE" == "0" ]; then
    echo "✅ Data seeding completed"
else
    echo "❌ Seeding failed (exit code: $EXIT_CODE)"
    echo "Check CloudWatch logs: /ecs/${PROJECT_NAME}-api"
    exit 1
fi
