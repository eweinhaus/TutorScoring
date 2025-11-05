#!/bin/bash
export PATH="/opt/homebrew/bin:$PATH"
set -e
source aws_config.env
REGION="${AWS_REGION:-us-east-1}"
PROJECT_NAME="${PROJECT_NAME:-tutor-scoring}"

echo "🔷 Setting up ECS..."

if [ -z "$API_REPO_URI" ] || [ -z "$WORKER_REPO_URI" ] || [ -z "$EXEC_ROLE_ARN" ] || [ -z "$DB_SECRET_ARN" ]; then
    echo "❌ Missing configuration. Run previous scripts first."
    exit 1
fi

# Create cluster
if ! aws ecs describe-clusters --clusters ${PROJECT_NAME}-cluster --region $REGION --query 'clusters[0].clusterName' --output text 2>/dev/null | grep -q ${PROJECT_NAME}-cluster; then
    aws ecs create-cluster \
        --cluster-name ${PROJECT_NAME}-cluster \
        --capacity-providers FARGATE \
        --default-capacity-provider-strategy capacityProvider=FARGATE,weight=1 \
        --region $REGION
fi

# Create log groups
aws logs create-log-group --log-group-name /ecs/${PROJECT_NAME}-api --region $REGION 2>/dev/null || true
aws logs create-log-group --log-group-name /ecs/${PROJECT_NAME}-worker --region $REGION 2>/dev/null || true

# Create API task definition
cat > /tmp/api-task-def.json <<EOF
{
  "family": "${PROJECT_NAME}-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "${EXEC_ROLE_ARN}",
  "taskRoleArn": "${TASK_ROLE_ARN}",
  "containerDefinitions": [{
    "name": "api",
    "image": "${API_REPO_URI}:latest",
    "essential": true,
    "portMappings": [{"containerPort": 8000, "protocol": "tcp"}],
    "environment": [
      {"name": "ENVIRONMENT", "value": "production"},
      {"name": "EMAIL_SERVICE", "value": "sendgrid"}
    ],
    "secrets": [
      {"name": "DATABASE_URL", "valueFrom": "${DB_SECRET_ARN}:DATABASE_URL::"},
      {"name": "REDIS_URL", "valueFrom": "${REDIS_SECRET_ARN}:REDIS_URL::"},
      {"name": "CELERY_BROKER_URL", "valueFrom": "${REDIS_SECRET_ARN}:REDIS_URL::"},
      {"name": "CELERY_RESULT_BACKEND", "valueFrom": "${REDIS_SECRET_ARN}:REDIS_URL::"},
      {"name": "SENDGRID_API_KEY", "valueFrom": "${APP_SECRET_ARN}:SENDGRID_API_KEY::"},
      {"name": "API_KEY", "valueFrom": "${APP_SECRET_ARN}:API_KEY::"},
      {"name": "SECRET_KEY", "valueFrom": "${APP_SECRET_ARN}:SECRET_KEY::"},
      {"name": "ADMIN_EMAIL", "valueFrom": "${APP_SECRET_ARN}:ADMIN_EMAIL::"}
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/${PROJECT_NAME}-api",
        "awslogs-region": "${REGION}",
        "awslogs-stream-prefix": "ecs"
      }
    },
    "healthCheck": {
      "command": ["CMD-SHELL", "curl -f http://localhost:8000/api/health || exit 1"],
      "interval": 30,
      "timeout": 5,
      "retries": 3,
      "startPeriod": 60
    }
  }]
}
EOF

aws ecs register-task-definition --cli-input-json file:///tmp/api-task-def.json --region $REGION >/dev/null

# Create worker task definition
cat > /tmp/worker-task-def.json <<EOF
{
  "family": "${PROJECT_NAME}-worker",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "${EXEC_ROLE_ARN}",
  "taskRoleArn": "${TASK_ROLE_ARN}",
  "containerDefinitions": [{
    "name": "worker",
    "image": "${WORKER_REPO_URI}:latest",
    "essential": true,
    "command": ["celery", "-A", "app.tasks.celery_app", "worker", "--loglevel=info"],
    "environment": [
      {"name": "ENVIRONMENT", "value": "production"},
      {"name": "EMAIL_SERVICE", "value": "sendgrid"}
    ],
    "secrets": [
      {"name": "DATABASE_URL", "valueFrom": "${DB_SECRET_ARN}:DATABASE_URL::"},
      {"name": "REDIS_URL", "valueFrom": "${REDIS_SECRET_ARN}:REDIS_URL::"},
      {"name": "CELERY_BROKER_URL", "valueFrom": "${REDIS_SECRET_ARN}:REDIS_URL::"},
      {"name": "CELERY_RESULT_BACKEND", "valueFrom": "${REDIS_SECRET_ARN}:REDIS_URL::"},
      {"name": "SENDGRID_API_KEY", "valueFrom": "${APP_SECRET_ARN}:SENDGRID_API_KEY::"},
      {"name": "API_KEY", "valueFrom": "${APP_SECRET_ARN}:API_KEY::"},
      {"name": "SECRET_KEY", "valueFrom": "${APP_SECRET_ARN}:SECRET_KEY::"},
      {"name": "ADMIN_EMAIL", "valueFrom": "${APP_SECRET_ARN}:ADMIN_EMAIL::"}
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/${PROJECT_NAME}-worker",
        "awslogs-region": "${REGION}",
        "awslogs-stream-prefix": "ecs"
      }
    }
  }]
}
EOF

aws ecs register-task-definition --cli-input-json file:///tmp/worker-task-def.json --region $REGION >/dev/null

rm -f /tmp/api-task-def.json /tmp/worker-task-def.json

echo "✅ ECS cluster and task definitions created"
