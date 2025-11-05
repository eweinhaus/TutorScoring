#!/bin/bash
export PATH="/opt/homebrew/bin:$PATH"
set -e
export PATH="/opt/homebrew/bin:$PATH"
source aws_config.env 2>/dev/null || true
REGION="${AWS_REGION:-us-east-1}"
PROJECT_NAME="${PROJECT_NAME:-tutor-scoring}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "🔷 Setting up ECR..."

# Authenticate Docker
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com

# Create repositories
if ! aws ecr describe-repositories --repository-names ${PROJECT_NAME}-api --region $REGION &>/dev/null; then
    aws ecr create-repository --repository-name ${PROJECT_NAME}-api --region $REGION
fi

if ! aws ecr describe-repositories --repository-names ${PROJECT_NAME}-worker --region $REGION &>/dev/null; then
    aws ecr create-repository --repository-name ${PROJECT_NAME}-worker --region $REGION
fi

API_REPO_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${PROJECT_NAME}-api"
WORKER_REPO_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${PROJECT_NAME}-worker"

# Build and push images
cd ../../backend

echo "🔷 Building API image (linux/amd64)..."
docker build --platform linux/amd64 -t ${PROJECT_NAME}-api:latest -f Dockerfile .
docker tag ${PROJECT_NAME}-api:latest ${API_REPO_URI}:latest
docker push ${API_REPO_URI}:latest

echo "🔷 Building Worker image (linux/amd64)..."
docker build --platform linux/amd64 -t ${PROJECT_NAME}-worker:latest -f Dockerfile.worker .
docker tag ${PROJECT_NAME}-worker:latest ${WORKER_REPO_URI}:latest
docker push ${WORKER_REPO_URI}:latest

cd ../scripts/aws_deploy

# Save to config
cat >> aws_config.env << EOF
export API_REPO_URI=$API_REPO_URI
export WORKER_REPO_URI=$WORKER_REPO_URI
EOF

echo "✅ Images pushed to ECR"
