#!/bin/bash
export PATH="/opt/homebrew/bin:$PATH"
set -e
source aws_config.env
REGION="${AWS_REGION:-us-east-1}"
PROJECT_NAME="${PROJECT_NAME:-tutor-scoring}"

echo "🔷 Syncing Local Database to Production..."
echo ""

# Get production database connection string from Secrets Manager
echo "📥 Fetching production database credentials..."
DB_SECRET=$(aws secretsmanager get-secret-value \
    --secret-id "$DB_SECRET_ARN" \
    --region $REGION \
    --query 'SecretString' \
    --output text 2>/dev/null)

if [ -z "$DB_SECRET" ]; then
    echo "❌ Failed to get database secret"
    exit 1
fi

PROD_DB_URL=$(echo "$DB_SECRET" | jq -r '.DATABASE_URL // empty')

if [ -z "$PROD_DB_URL" ]; then
    echo "❌ DATABASE_URL not found in secret"
    exit 1
fi

# Get local database URL
cd ../../backend
if [ -f .env ]; then
    LOCAL_DB_URL=$(grep "^DATABASE_URL=" .env 2>/dev/null | cut -d'=' -f2- | tr -d '"' || echo "")
fi

if [ -z "$LOCAL_DB_URL" ]; then
    LOCAL_DB_URL="postgresql://$(whoami)@localhost:5432/tutor_scoring"
    echo "⚠️  Using default local DB URL: $LOCAL_DB_URL"
fi

echo "✅ Local DB: ${LOCAL_DB_URL%%@*}@***"
echo "✅ Prod DB: ${PROD_DB_URL%%@*}@***"
echo ""

# Confirm before proceeding
if [ "$1" != "--yes" ]; then
    read -p "⚠️  This will REPLACE all production data with local data. Continue? (yes/no): " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        echo "❌ Aborted"
        exit 0
    fi
fi

echo ""
echo "🔷 Starting data sync..."

# Create temporary directory for dump files
TMP_DIR=$(mktemp -d)
trap "rm -rf $TMP_DIR" EXIT

DUMP_FILE="$TMP_DIR/local_dump.sql"

echo "📤 Step 1/4: Exporting local database..."
DUMP_OUTPUT=$(pg_dump "$LOCAL_DB_URL" \
    --clean \
    --if-exists \
    --no-owner \
    --no-acl \
    --format=plain \
    --file="$DUMP_FILE" 2>&1)

if echo "$DUMP_OUTPUT" | grep -qi "error\|fatal\|failed"; then
    echo "❌ Export failed:"
    echo "$DUMP_OUTPUT" | grep -i "error\|fatal\|failed" | head -5
    exit 1
fi

if [ ! -s "$DUMP_FILE" ]; then
    echo "❌ Export produced empty file"
    exit 1
fi

FILE_SIZE=$(du -h "$DUMP_FILE" | cut -f1)
echo "✅ Export complete: $FILE_SIZE"
echo ""

# Upload to S3 for ECS task access
S3_BUCKET="${PROJECT_NAME}-data-sync"
S3_KEY="sync/dump-$(date +%s).sql"

echo "📤 Step 2/4: Uploading dump to S3..."
aws s3 mb "s3://${S3_BUCKET}" --region $REGION 2>/dev/null || true
aws s3 cp "$DUMP_FILE" "s3://${S3_BUCKET}/${S3_KEY}" --region $REGION > /dev/null
echo "✅ Upload complete: s3://${S3_BUCKET}/${S3_KEY}"
echo ""

# Create import script
IMPORT_SCRIPT="$TMP_DIR/import.sh"
cat > "$IMPORT_SCRIPT" << 'IMPORTEOF'
#!/bin/bash
set -e
pip install boto3 > /dev/null 2>&1 || true
python3 << 'PYEOF'
import boto3
import subprocess
import os
import sys

s3_bucket = os.environ.get('S3_BUCKET')
s3_key = os.environ.get('S3_KEY')
db_url = os.environ.get('DATABASE_URL')

if not all([s3_bucket, s3_key, db_url]):
    print("Missing environment variables", file=sys.stderr)
    sys.exit(1)

print(f"Downloading s3://{s3_bucket}/{s3_key}...")
s3 = boto3.client('s3')
s3.download_file(s3_bucket, s3_key, '/tmp/dump.sql')
print("Download complete")

print("Importing to database...")
result = subprocess.run(
    ['psql', db_url, '-f', '/tmp/dump.sql'],
    capture_output=True,
    text=True
)

if result.returncode != 0:
    print(f"Import failed: {result.stderr}", file=sys.stderr)
    sys.exit(1)

print("Import complete")
PYEOF
IMPORTEOF

# Upload import script to S3
SCRIPT_KEY="sync/import.sh"
aws s3 cp "$IMPORT_SCRIPT" "s3://${S3_BUCKET}/${SCRIPT_KEY}" --region $REGION > /dev/null
chmod +x "$IMPORT_SCRIPT"

echo "🔄 Step 3/4: Running import via ECS task..."
TASK_ARN=$(aws ecs run-task \
    --cluster ${PROJECT_NAME}-cluster \
    --task-definition ${PROJECT_NAME}-api \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[${PRIV_SUBNET_1},${PRIV_SUBNET_2}],securityGroups=[${API_SG}],assignPublicIp=ENABLED}" \
    --overrides "{
        \"containerOverrides\": [{
            \"name\": \"api\",
            \"command\": [\"sh\", \"-c\", \"pip install boto3 && python3 -c \\\"import boto3, subprocess, os; s3=boto3.client('s3'); s3.download_file('${S3_BUCKET}', '${S3_KEY}', '/tmp/dump.sql'); subprocess.run(['psql', os.environ['DATABASE_URL'], '-f', '/tmp/dump.sql'], check=True)\\\"\"],
            \"environment\": [
                {\"name\": \"DATABASE_URL\", \"value\": \"${PROD_DB_URL}\"},
                {\"name\": \"S3_BUCKET\", \"value\": \"${S3_BUCKET}\"},
                {\"name\": \"S3_KEY\", \"value\": \"${S3_KEY}\"}
            ]
        }]
    }" \
    --region $REGION \
    --query 'tasks[0].taskArn' --output text 2>/dev/null || echo "")

if [ -z "$TASK_ARN" ] || [ "$TASK_ARN" == "None" ]; then
    echo "❌ Failed to start ECS task"
    exit 1
fi

echo "⏳ Task started: $TASK_ARN"
echo "⏳ Waiting for completion (this may take 5-10 minutes)..."

aws ecs wait tasks-stopped --cluster ${PROJECT_NAME}-cluster --tasks $TASK_ARN --region $REGION

EXIT_CODE=$(aws ecs describe-tasks --cluster ${PROJECT_NAME}-cluster --tasks $TASK_ARN --region $REGION --query 'tasks[0].containers[0].exitCode' --output text)

if [ "$EXIT_CODE" != "0" ]; then
    echo "❌ Import failed (exit code: $EXIT_CODE)"
    echo "Check CloudWatch logs: /ecs/${PROJECT_NAME}-api"
    echo "Task ARN: $TASK_ARN"
    
    # Get logs
    LOG_STREAM=$(aws logs describe-log-streams \
        --log-group-name "/ecs/${PROJECT_NAME}-api" \
        --order-by LastEventTime \
        --descending \
        --max-items 1 \
        --region $REGION \
        --query 'logStreams[0].logStreamName' \
        --output text 2>/dev/null || echo "")
    
    if [ -n "$LOG_STREAM" ] && [ "$LOG_STREAM" != "None" ]; then
        echo ""
        echo "Recent logs:"
        aws logs get-log-events \
            --log-group-name "/ecs/${PROJECT_NAME}-api" \
            --log-stream-name "$LOG_STREAM" \
            --region $REGION \
            --limit 20 \
            --query 'events[*].message' \
            --output text 2>/dev/null | tail -10
    fi
    
    exit 1
fi

echo "✅ Import complete"
echo ""

# Cleanup S3
echo "🧹 Step 4/4: Cleaning up..."
aws s3 rm "s3://${S3_BUCKET}/${S3_KEY}" --region $REGION > /dev/null 2>&1 || true
aws s3 rm "s3://${S3_BUCKET}/${SCRIPT_KEY}" --region $REGION > /dev/null 2>&1 || true
echo "✅ Cleanup complete"
echo ""

echo "✅ Data sync complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Verify data in production: https://d2iu6aqgs7qt5d.cloudfront.net"
echo "   2. Clear CloudFront cache if needed"
echo "   3. Restart ECS services if data doesn't appear"

cd ../scripts/aws_deploy
