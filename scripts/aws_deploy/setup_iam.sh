#!/bin/bash
export PATH="/opt/homebrew/bin:$PATH"
set -e
source aws_config.env 2>/dev/null || true
REGION="${AWS_REGION:-us-east-1}"
PROJECT_NAME="${PROJECT_NAME:-tutor-scoring}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

echo "🔷 Setting up IAM Roles..."

# Create trust policy
cat > /tmp/ecs-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "ecs-tasks.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
EOF

# Create execution role
EXEC_ROLE_NAME="${PROJECT_NAME}-ecs-task-execution-role"
if ! aws iam get-role --role-name $EXEC_ROLE_NAME &>/dev/null; then
    EXEC_ROLE_ARN=$(aws iam create-role \
        --role-name $EXEC_ROLE_NAME \
        --assume-role-policy-document file:///tmp/ecs-trust-policy.json \
        --query 'Role.Arn' --output text)
    
    aws iam attach-role-policy \
        --role-name $EXEC_ROLE_NAME \
        --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
    
    # Create secrets policy
    cat > /tmp/secrets-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"],
    "Resource": "arn:aws:secretsmanager:${REGION}:${AWS_ACCOUNT_ID}:secret:${PROJECT_NAME}/*"
  }]
}
EOF
    
    POLICY_ARN=$(aws iam create-policy \
        --policy-name ${PROJECT_NAME}-secrets-access \
        --policy-document file:///tmp/secrets-policy.json \
        --query 'Policy.Arn' --output text)
    
    aws iam attach-role-policy --role-name $EXEC_ROLE_NAME --policy-arn $POLICY_ARN
else
    EXEC_ROLE_ARN=$(aws iam get-role --role-name $EXEC_ROLE_NAME --query 'Role.Arn' --output text)
fi

# Create task role
TASK_ROLE_NAME="${PROJECT_NAME}-ecs-task-role"
if ! aws iam get-role --role-name $TASK_ROLE_NAME &>/dev/null; then
    TASK_ROLE_ARN=$(aws iam create-role \
        --role-name $TASK_ROLE_NAME \
        --assume-role-policy-document file:///tmp/ecs-trust-policy.json \
        --query 'Role.Arn' --output text)
    
    aws iam attach-role-policy --role-name $TASK_ROLE_NAME --policy-arn $POLICY_ARN
else
    TASK_ROLE_ARN=$(aws iam get-role --role-name $TASK_ROLE_NAME --query 'Role.Arn' --output text)
fi

rm -f /tmp/ecs-trust-policy.json /tmp/secrets-policy.json

# Save to config
cat >> aws_config.env << EOF
export EXEC_ROLE_ARN=$EXEC_ROLE_ARN
export TASK_ROLE_ARN=$TASK_ROLE_ARN
EOF

echo "✅ IAM roles created"
