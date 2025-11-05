#!/bin/bash
export PATH="/opt/homebrew/bin:$PATH"
set -e
source aws_config.env
REGION="${AWS_REGION:-us-east-1}"
PROJECT_NAME="${PROJECT_NAME:-tutor-scoring}"

echo "🔷 Setting up ALB..."

if [ -z "$VPC_ID" ] || [ -z "$PUB_SUBNET_1" ] || [ -z "$ALB_SG" ]; then
    echo "❌ Missing configuration. Run setup_infrastructure.sh first."
    exit 1
fi

# Create target group
TG_NAME="${PROJECT_NAME}-api-tg"
if ! aws elbv2 describe-target-groups --names $TG_NAME --region $REGION &>/dev/null; then
    TG_ARN=$(aws elbv2 create-target-group \
        --name $TG_NAME \
        --protocol HTTP \
        --port 8000 \
        --vpc-id $VPC_ID \
        --target-type ip \
        --health-check-path /api/health \
        --health-check-protocol HTTP \
        --health-check-port 8000 \
        --healthy-threshold-count 2 \
        --unhealthy-threshold-count 3 \
        --health-check-timeout-seconds 5 \
        --health-check-interval-seconds 30 \
        --region $REGION \
        --query 'TargetGroups[0].TargetGroupArn' --output text)
else
    TG_ARN=$(aws elbv2 describe-target-groups --names $TG_NAME --region $REGION --query 'TargetGroups[0].TargetGroupArn' --output text)
fi

# Create load balancer
ALB_NAME="${PROJECT_NAME}-alb"
if ! aws elbv2 describe-load-balancers --names $ALB_NAME --region $REGION &>/dev/null; then
    ALB_ARN=$(aws elbv2 create-load-balancer \
        --name $ALB_NAME \
        --subnets $PUB_SUBNET_1 $PUB_SUBNET_2 \
        --security-groups $ALB_SG \
        --scheme internet-facing \
        --type application \
        --ip-address-type ipv4 \
        --region $REGION \
        --query 'LoadBalancers[0].LoadBalancerArn' --output text)
    
    echo "⏳ Waiting for ALB..."
    aws elbv2 wait load-balancer-available --load-balancer-arns $ALB_ARN --region $REGION
    
    ALB_DNS=$(aws elbv2 describe-load-balancers --load-balancer-arns $ALB_ARN --region $REGION --query 'LoadBalancers[0].DNSName' --output text)
else
    ALB_ARN=$(aws elbv2 describe-load-balancers --names $ALB_NAME --region $REGION --query 'LoadBalancers[0].LoadBalancerArn' --output text)
    ALB_DNS=$(aws elbv2 describe-load-balancers --names $ALB_NAME --region $REGION --query 'LoadBalancers[0].DNSName' --output text)
fi

# Create listener
if ! aws elbv2 describe-listeners --load-balancer-arn $ALB_ARN --region $REGION --query 'Listeners[?Port==`80`]' --output text | grep -q 80; then
    aws elbv2 create-listener \
        --load-balancer-arn $ALB_ARN \
        --protocol HTTP \
        --port 80 \
        --default-actions Type=forward,TargetGroupArn=$TG_ARN \
        --region $REGION >/dev/null
fi

# Save to config
cat >> aws_config.env << EOF
export TG_ARN=$TG_ARN
export ALB_ARN=$ALB_ARN
export ALB_DNS=$ALB_DNS
EOF

echo "✅ ALB created: http://$ALB_DNS"
