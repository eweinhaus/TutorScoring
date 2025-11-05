#!/bin/bash
# Use Existing VPC Script
export PATH="/opt/homebrew/bin:$PATH"

REGION="${AWS_REGION:-us-east-1}"

echo "🔍 Checking for existing VPCs..."
echo ""

VPC_LIST=$(aws ec2 describe-vpcs --region $REGION --query 'Vpcs[*].[VpcId,CidrBlock,Tags[?Key==`Name`].Value|[0]]' --output text)

if [ -z "$VPC_LIST" ]; then
    echo "❌ No VPCs found"
    exit 1
fi

echo "Available VPCs:"
echo "$VPC_LIST" | awk '{printf "  %d. %s (%s) - %s\n", NR, $1, $2, $3}'
echo ""

# Check if tutor-scoring-vpc already exists
EXISTING_VPC=$(aws ec2 describe-vpcs --region $REGION --filters "Name=tag:Name,Values=tutor-scoring-vpc" --query 'Vpcs[0].VpcId' --output text 2>/dev/null)

if [ ! -z "$EXISTING_VPC" ] && [ "$EXISTING_VPC" != "None" ]; then
    echo "✅ Found existing tutor-scoring-vpc: $EXISTING_VPC"
    echo "Using existing VPC..."
    VPC_ID=$EXISTING_VPC
else
    echo "No tutor-scoring-vpc found. Please select a VPC to use:"
    read -p "Enter VPC ID (or press Enter to use default): " SELECTED_VPC
    
    if [ -z "$SELECTED_VPC" ]; then
        # Use first VPC
        VPC_ID=$(echo "$VPC_LIST" | head -1 | awk '{print $1}')
        echo "Using first VPC: $VPC_ID"
    else
        VPC_ID=$SELECTED_VPC
    fi
fi

# Get subnets for this VPC
SUBNETS=$(aws ec2 describe-subnets --region $REGION --filters "Name=vpc-id,Values=$VPC_ID" --query 'Subnets[*].[SubnetId,AvailabilityZone,CidrBlock,Tags[?Key==`Name`].Value|[0]]' --output text)

echo ""
echo "Subnets in VPC $VPC_ID:"
echo "$SUBNETS" | awk '{printf "  %s (%s) - %s - %s\n", $1, $2, $3, $4}'

# Save to config
cat > aws_config.env << EOF
export AWS_REGION=$REGION
export VPC_ID=$VPC_ID
export PROJECT_NAME=tutor-scoring
EOF

echo ""
echo "✅ Configuration saved to aws_config.env"
echo "   VPC_ID=$VPC_ID"
echo ""
echo "⚠️  Note: You may need to:"
echo "   1. Create subnets if they don't exist"
echo "   2. Create Internet Gateway if not attached"
echo "   3. Create NAT Gateway if needed"
echo ""
echo "Continuing with infrastructure setup..."

