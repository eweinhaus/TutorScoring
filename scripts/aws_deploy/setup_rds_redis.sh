#!/bin/bash
export PATH="/opt/homebrew/bin:$PATH"
set -e
source aws_config.env 2>/dev/null || true
REGION="${AWS_REGION:-us-east-1}"
PROJECT_NAME="${PROJECT_NAME:-tutor-scoring}"
DB_INSTANCE_CLASS="${DB_INSTANCE_CLASS:-db.t3.micro}"
REDIS_NODE_TYPE="${REDIS_NODE_TYPE:-cache.t3.micro}"

echo "🔷 Setting up RDS and ElastiCache..."

if [ -z "$VPC_ID" ] || [ -z "$PRIV_SUBNET_1" ] || [ -z "$PRIV_SUBNET_2" ]; then
    echo "❌ VPC/subnets not set. Run setup_infrastructure.sh first."
    exit 1
fi

# Create DB subnet group
if ! aws rds describe-db-subnet-groups --db-subnet-group-name ${PROJECT_NAME}-db-subnet-group --region $REGION &>/dev/null; then
    aws rds create-db-subnet-group \
        --db-subnet-group-name ${PROJECT_NAME}-db-subnet-group \
        --db-subnet-group-description "DB subnet group" \
        --subnet-ids $PRIV_SUBNET_1 $PRIV_SUBNET_2 \
        --region $REGION
fi

# Generate password if not set
if [ -z "$DB_PASSWORD" ]; then
    DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
fi

# Create RDS instance
if ! aws rds describe-db-instances --db-instance-identifier ${PROJECT_NAME}-db --region $REGION &>/dev/null; then
    echo "⏳ Creating RDS instance (takes 10-15 minutes)..."
    aws rds create-db-instance \
        --db-instance-identifier ${PROJECT_NAME}-db \
        --db-instance-class $DB_INSTANCE_CLASS \
        --engine postgres \
        --engine-version 14.19 \
        --master-username tutor_admin \
        --master-user-password "$DB_PASSWORD" \
        --allocated-storage 20 \
        --storage-type gp3 \
        --db-name tutor_scoring \
        --db-subnet-group-name ${PROJECT_NAME}-db-subnet-group \
        --vpc-security-group-ids $DB_SG \
        --backup-retention-period 7 \
        --storage-encrypted \
        --no-publicly-accessible \
        --region $REGION \
        --tags "Key=Name,Value=${PROJECT_NAME}-db"
    
    echo "⏳ Waiting for RDS to become available..."
    aws rds wait db-instance-available --db-instance-identifier ${PROJECT_NAME}-db --region $REGION
fi

DB_ENDPOINT=$(aws rds describe-db-instances --db-instance-identifier ${PROJECT_NAME}-db --region $REGION --query 'DBInstances[0].Endpoint.Address' --output text)

# Create cache subnet group
if ! aws elasticache describe-cache-subnet-groups --cache-subnet-group-name ${PROJECT_NAME}-cache-subnet-group --region $REGION &>/dev/null; then
    aws elasticache create-cache-subnet-group \
        --cache-subnet-group-name ${PROJECT_NAME}-cache-subnet-group \
        --cache-subnet-group-description "Cache subnet group" \
        --subnet-ids $PRIV_SUBNET_1 $PRIV_SUBNET_2 \
        --region $REGION
fi

# Create Redis cluster
if ! aws elasticache describe-cache-clusters --cache-cluster-id ${PROJECT_NAME}-redis --region $REGION &>/dev/null; then
    echo "⏳ Creating Redis cluster (takes 5-10 minutes)..."
    aws elasticache create-cache-cluster \
        --cache-cluster-id ${PROJECT_NAME}-redis \
        --engine redis \
        --engine-version 7.0 \
        --cache-node-type $REDIS_NODE_TYPE \
        --num-cache-nodes 1 \
        --cache-subnet-group-name ${PROJECT_NAME}-cache-subnet-group \
        --security-group-ids $REDIS_SG \
        --region $REGION \
        --tags "Key=Name,Value=${PROJECT_NAME}-redis"
    
    echo "⏳ Waiting for Redis to become available..."
    aws elasticache wait cache-cluster-available --cache-cluster-id ${PROJECT_NAME}-redis --region $REGION
fi

REDIS_ENDPOINT=$(aws elasticache describe-cache-clusters --cache-cluster-id ${PROJECT_NAME}-redis --region $REGION --show-cache-node-info --query 'CacheClusters[0].CacheNodes[0].Endpoint.Address' --output text)

# Save to config
cat >> aws_config.env << EOF
export DB_ENDPOINT=$DB_ENDPOINT
export REDIS_ENDPOINT=$REDIS_ENDPOINT
export DB_PASSWORD=$DB_PASSWORD
EOF

echo "✅ RDS: $DB_ENDPOINT"
echo "✅ Redis: $REDIS_ENDPOINT:6379"
