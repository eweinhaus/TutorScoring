#!/bin/bash
export PATH="/opt/homebrew/bin:$PATH"
# Update CORS Configuration Script

set -e

# Load configuration
if [ -f aws_config.env ]; then
    source aws_config.env
fi

REGION="${AWS_REGION:-us-east-1}"
PROJECT_NAME="${PROJECT_NAME:-tutor-scoring}"

echo "🔧 Updating CORS Configuration"
echo "Region: $REGION"
echo ""

if [ -z "$CLOUDFRONT_URL" ]; then
    echo "❌ CloudFront URL not found in config. Run deploy_frontend.sh first."
    exit 1
fi

if [ -z "$APP_SECRET_ARN" ]; then
    echo "❌ App secrets ARN not found. Run setup_secrets.sh first."
    exit 1
fi

# Update secrets with CORS_ORIGINS
echo "🔷 Updating CORS_ORIGINS in secrets..."

# Get current secrets
CURRENT_SECRETS=$(aws secretsmanager get-secret-value \
    --secret-id ${APP_SECRET_ARN} \
    --region $REGION \
    --query 'SecretString' \
    --output text)

# Add CORS_ORIGINS if jq is available, otherwise use sed
if command -v jq &> /dev/null; then
    UPDATED_SECRETS=$(echo "$CURRENT_SECRETS" | jq ". + {\"CORS_ORIGINS\": \"${CLOUDFRONT_URL}\"}")
else
    # Fallback: simple JSON manipulation without jq
    # Remove closing brace, add CORS_ORIGINS, add closing brace
    UPDATED_SECRETS=$(echo "$CURRENT_SECRETS" | sed 's/}$//')
    UPDATED_SECRETS="${UPDATED_SECRETS}, \"CORS_ORIGINS\": \"${CLOUDFRONT_URL}\"}"
fi

aws secretsmanager update-secret \
    --secret-id ${APP_SECRET_ARN} \
    --secret-string "$UPDATED_SECRETS" \
    --region $REGION > /dev/null

echo "✅ Secrets updated with CORS_ORIGINS: $CLOUDFRONT_URL"

# Get current task definition
echo ""
echo "🔷 Updating API task definition..."

CURRENT_TASK_DEF=$(aws ecs describe-task-definition \
    --task-definition ${PROJECT_NAME}-api \
    --region $REGION \
    --query 'taskDefinition' \
    --output json)

# Update task definition to include CORS_ORIGINS from secrets
UPDATED_TASK_DEF=$(echo "$CURRENT_TASK_DEF" | jq '
    .containerDefinitions[0].secrets += [
        {
            "name": "CORS_ORIGINS",
            "valueFrom": ($APP_SECRET_ARN + ":CORS_ORIGINS::")
        }
    ] |
    .containerDefinitions[0].environment = [
        {
            "name": "ENVIRONMENT",
            "value": "production"
        },
        {
            "name": "EMAIL_SERVICE",
            "value": "sendgrid"
        }
    ]
' --arg APP_SECRET_ARN "$APP_SECRET_ARN")

# Remove fields that can't be in new task definition
UPDATED_TASK_DEF=$(echo "$UPDATED_TASK_DEF" | jq 'del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .compatibilities, .registeredAt, .registeredBy)')

# Register new task definition
NEW_TASK_DEF_REVISION=$(aws ecs register-task-definition \
    --cli-input-json "$UPDATED_TASK_DEF" \
    --region $REGION \
    --query 'taskDefinition.revision' \
    --output text)

echo "✅ New task definition revision: $NEW_TASK_DEF_REVISION"

# Update service to use new task definition
echo ""
echo "🔷 Updating API service..."

aws ecs update-service \
    --cluster ${PROJECT_NAME}-cluster \
    --service ${PROJECT_NAME}-api-service \
    --task-definition ${PROJECT_NAME}-api:$NEW_TASK_DEF_REVISION \
    --region $REGION > /dev/null

echo "✅ Service update initiated"
echo "⏳ Waiting for service to stabilize..."

aws ecs wait services-stable \
    --cluster ${PROJECT_NAME}-cluster \
    --services ${PROJECT_NAME}-api-service \
    --region $REGION

echo "✅ Service updated and stable"

echo ""
echo "✅ CORS configuration update complete!"
echo "   CORS_ORIGINS: $CLOUDFRONT_URL"

