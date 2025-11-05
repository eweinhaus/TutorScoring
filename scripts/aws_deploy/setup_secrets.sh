#!/bin/bash
export PATH="/opt/homebrew/bin:$PATH"
set -e
source aws_config.env 2>/dev/null || true
REGION="${AWS_REGION:-us-east-1}"
PROJECT_NAME="${PROJECT_NAME:-tutor-scoring}"

echo "🔷 Setting up Secrets Manager..."

if [ -z "$DB_ENDPOINT" ] || [ -z "$REDIS_ENDPOINT" ] || [ -z "$DB_PASSWORD" ]; then
    echo "❌ Database/Redis not set. Run setup_rds_redis.sh first."
    exit 1
fi

# Use provided admin email or default
ADMIN_EMAIL="${ADMIN_EMAIL:-etweinhaus@gmail.com}"

# Generate keys if not set
if [ -z "$API_KEY" ]; then
    API_KEY=$(openssl rand -hex 32)
fi
if [ -z "$SECRET_KEY" ]; then
    SECRET_KEY=$(openssl rand -hex 32)
fi

# Prompt for SendGrid API key only if not set
if [ -z "$SENDGRID_API_KEY" ]; then
    echo ""
    echo "📝 SendGrid API Key Required"
    echo "   You can get this from https://app.sendgrid.com/settings/api_keys"
    echo "   Or press Enter to skip (emails will not work)"
    read -sp "Enter SendGrid API Key (or press Enter to skip): " SENDGRID_API_KEY
    echo ""
    if [ -z "$SENDGRID_API_KEY" ]; then
        SENDGRID_API_KEY="placeholder-key-will-need-update"
        echo "⚠️  Using placeholder - update later in Secrets Manager"
    fi
fi

# Create database secret
DATABASE_URL="postgresql://tutor_admin:${DB_PASSWORD}@${DB_ENDPOINT}:5432/tutor_scoring"
if ! aws secretsmanager describe-secret --secret-id ${PROJECT_NAME}/database --region $REGION &>/dev/null; then
    aws secretsmanager create-secret \
        --name ${PROJECT_NAME}/database \
        --description "Database connection" \
        --secret-string "{\"DATABASE_URL\":\"${DATABASE_URL}\"}" \
        --region $REGION
else
    aws secretsmanager update-secret \
        --secret-id ${PROJECT_NAME}/database \
        --secret-string "{\"DATABASE_URL\":\"${DATABASE_URL}\"}" \
        --region $REGION
fi

# Create Redis secret
REDIS_URL="redis://${REDIS_ENDPOINT}:6379/0"
if ! aws secretsmanager describe-secret --secret-id ${PROJECT_NAME}/redis --region $REGION &>/dev/null; then
    aws secretsmanager create-secret \
        --name ${PROJECT_NAME}/redis \
        --description "Redis connection" \
        --secret-string "{\"REDIS_URL\":\"${REDIS_URL}\"}" \
        --region $REGION
else
    aws secretsmanager update-secret \
        --secret-id ${PROJECT_NAME}/redis \
        --secret-string "{\"REDIS_URL\":\"${REDIS_URL}\"}" \
        --region $REGION
fi

# Create app secrets
APP_SECRETS=$(cat <<EOF
{
  "SENDGRID_API_KEY": "${SENDGRID_API_KEY}",
  "API_KEY": "${API_KEY}",
  "SECRET_KEY": "${SECRET_KEY}",
  "ADMIN_EMAIL": "${ADMIN_EMAIL}"
}
EOF
)

if ! aws secretsmanager describe-secret --secret-id ${PROJECT_NAME}/app-secrets --region $REGION &>/dev/null; then
    aws secretsmanager create-secret \
        --name ${PROJECT_NAME}/app-secrets \
        --description "App secrets" \
        --secret-string "$APP_SECRETS" \
        --region $REGION
else
    aws secretsmanager update-secret \
        --secret-id ${PROJECT_NAME}/app-secrets \
        --secret-string "$APP_SECRETS" \
        --region $REGION
fi

# Get ARNs
DB_SECRET_ARN=$(aws secretsmanager describe-secret --secret-id ${PROJECT_NAME}/database --region $REGION --query 'ARN' --output text)
REDIS_SECRET_ARN=$(aws secretsmanager describe-secret --secret-id ${PROJECT_NAME}/redis --region $REGION --query 'ARN' --output text)
APP_SECRET_ARN=$(aws secretsmanager describe-secret --secret-id ${PROJECT_NAME}/app-secrets --region $REGION --query 'ARN' --output text)

# Save to config
cat >> aws_config.env << EOF
export DB_SECRET_ARN=$DB_SECRET_ARN
export REDIS_SECRET_ARN=$REDIS_SECRET_ARN
export APP_SECRET_ARN=$APP_SECRET_ARN
export API_KEY=$API_KEY
export ADMIN_EMAIL=$ADMIN_EMAIL
EOF

echo "✅ Secrets created"
echo "   API Key: $API_KEY (save this!)"
