#!/bin/bash
export PATH="/opt/homebrew/bin:$PATH"
set +e  # Don't exit on error initially
source aws_config.env 2>/dev/null || true
set +e  # Keep flexible for AWS limit errors - we'll handle them explicitly
REGION="${AWS_REGION:-us-east-1}"
PROJECT_NAME="${PROJECT_NAME:-tutor-scoring}"
VPC_CIDR="10.0.0.0/16"

echo "🔷 Creating Infrastructure..."

# Get availability zones
AZ1=$(aws ec2 describe-availability-zones --region $REGION --query 'AvailabilityZones[0].ZoneName' --output text)
AZ2=$(aws ec2 describe-availability-zones --region $REGION --query 'AvailabilityZones[1].ZoneName' --output text)

# Create or get VPC
if [ -z "$VPC_ID" ]; then
    VPC_ID=$(aws ec2 describe-vpcs --filters "Name=tag:Name,Values=${PROJECT_NAME}-vpc" --region $REGION --query 'Vpcs[0].VpcId' --output text 2>/dev/null)
    if [ -z "$VPC_ID" ] || [ "$VPC_ID" == "None" ]; then
        # Try to create new VPC, but if limit exceeded, use default VPC
        VPC_ID=$(aws ec2 create-vpc --cidr-block $VPC_CIDR --region $REGION --query 'Vpc.VpcId' --output text 2>&1)
        if echo "$VPC_ID" | grep -q "VpcLimitExceeded"; then
            echo "⚠️  VPC limit exceeded. Using default VPC..."
            VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --region $REGION --query 'Vpcs[0].VpcId' --output text)
            echo "   Using VPC: $VPC_ID"
        else
            aws ec2 create-tags --resources $VPC_ID --tags Key=Name,Value=${PROJECT_NAME}-vpc --region $REGION
        fi
    fi
fi
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-hostnames --region $REGION 2>/dev/null || true
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-support --region $REGION 2>/dev/null || true

# Create or get Internet Gateway
IGW_ID=$(aws ec2 describe-internet-gateways --filters "Name=tag:Name,Values=${PROJECT_NAME}-igw" --region $REGION --query 'InternetGateways[0].InternetGatewayId' --output text 2>/dev/null)
if [ -z "$IGW_ID" ] || [ "$IGW_ID" == "None" ]; then
    # Check if VPC already has an IGW attached
    IGW_ID=$(aws ec2 describe-internet-gateways --filters "Name=attachment.vpc-id,Values=$VPC_ID" --region $REGION --query 'InternetGateways[0].InternetGatewayId' --output text 2>/dev/null)
    if [ -z "$IGW_ID" ] || [ "$IGW_ID" == "None" ]; then
        # Try to create new IGW
        IGW_ID=$(aws ec2 create-internet-gateway --region $REGION --query 'InternetGateway.InternetGatewayId' --output text 2>&1)
        if echo "$IGW_ID" | grep -q "InternetGatewayLimitExceeded"; then
            echo "⚠️  Internet Gateway limit exceeded. Checking for existing unattached IGW..."
            IGW_ID=$(aws ec2 describe-internet-gateways --region $REGION --query 'InternetGateways[?Attachments==`[]`].[InternetGatewayId] | [0][0]' --output text 2>/dev/null)
            if [ -z "$IGW_ID" ] || [ "$IGW_ID" == "None" ]; then
                echo "❌ No available Internet Gateway found. Please create one manually or increase limit."
                exit 1
            else
                echo "   Using existing unattached IGW: $IGW_ID"
                aws ec2 attach-internet-gateway --internet-gateway-id $IGW_ID --vpc-id $VPC_ID --region $REGION
            fi
        else
            aws ec2 create-tags --resources $IGW_ID --tags Key=Name,Value=${PROJECT_NAME}-igw --region $REGION
            aws ec2 attach-internet-gateway --internet-gateway-id $IGW_ID --vpc-id $VPC_ID --region $REGION
        fi
    else
        echo "   Using existing IGW attached to VPC: $IGW_ID"
    fi
fi

# Get VPC CIDR to determine subnet ranges
VPC_CIDR_BLOCK=$(aws ec2 describe-vpcs --vpc-ids $VPC_ID --region $REGION --query 'Vpcs[0].CidrBlock' --output text)
echo "   VPC CIDR: $VPC_CIDR_BLOCK"

# Create or get subnets - use existing subnets if they exist, otherwise create new ones
PUB_SUBNET_1=$(aws ec2 describe-subnets --filters "Name=tag:Name,Values=${PROJECT_NAME}-public-1a" --region $REGION --query 'Subnets[0].SubnetId' --output text 2>/dev/null)
if [ -z "$PUB_SUBNET_1" ] || [ "$PUB_SUBNET_1" == "None" ]; then
    # Check if VPC CIDR is 10.0.0.0/16, if not, use existing subnets
    if echo "$VPC_CIDR_BLOCK" | grep -q "^10\.0\.0\.0/16$"; then
        PUB_SUBNET_1=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.1.0/24 --availability-zone $AZ1 --region $REGION --query 'Subnet.SubnetId' --output text 2>&1)
        if echo "$PUB_SUBNET_1" | grep -q "error\|Error\|InvalidCidrBlock"; then
            echo "⚠️  Subnet creation failed, using existing subnet in $AZ1"
            PUB_SUBNET_1=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" "Name=availability-zone,Values=$AZ1" --region $REGION --query 'Subnets[0].SubnetId' --output text)
        else
            aws ec2 create-tags --resources $PUB_SUBNET_1 --tags Key=Name,Value=${PROJECT_NAME}-public-1a --region $REGION
        fi
    else
        echo "   Using existing subnet in $AZ1 (VPC CIDR: $VPC_CIDR_BLOCK)"
        PUB_SUBNET_1=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" "Name=availability-zone,Values=$AZ1" --region $REGION --query 'Subnets[0].SubnetId' --output text)
    fi
fi

PUB_SUBNET_2=$(aws ec2 describe-subnets --filters "Name=tag:Name,Values=${PROJECT_NAME}-public-1b" --region $REGION --query 'Subnets[0].SubnetId' --output text 2>/dev/null)
if [ -z "$PUB_SUBNET_2" ] || [ "$PUB_SUBNET_2" == "None" ]; then
    if echo "$VPC_CIDR_BLOCK" | grep -q "^10\.0\.0\.0/16$"; then
        PUB_SUBNET_2=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.2.0/24 --availability-zone $AZ2 --region $REGION --query 'Subnet.SubnetId' --output text 2>&1)
        if echo "$PUB_SUBNET_2" | grep -q "error\|Error\|InvalidCidrBlock"; then
            echo "⚠️  Subnet creation failed, using existing subnet in $AZ2"
            PUB_SUBNET_2=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" "Name=availability-zone,Values=$AZ2" --region $REGION --query 'Subnets[0].SubnetId' --output text)
        else
            aws ec2 create-tags --resources $PUB_SUBNET_2 --tags Key=Name,Value=${PROJECT_NAME}-public-1b --region $REGION
        fi
    else
        echo "   Using existing subnet in $AZ2 (VPC CIDR: $VPC_CIDR_BLOCK)"
        PUB_SUBNET_2=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" "Name=availability-zone,Values=$AZ2" --region $REGION --query 'Subnets[0].SubnetId' --output text)
    fi
fi

# For private subnets, use public subnets if we can't create dedicated private ones
PRIV_SUBNET_1=$(aws ec2 describe-subnets --filters "Name=tag:Name,Values=${PROJECT_NAME}-private-1a" --region $REGION --query 'Subnets[0].SubnetId' --output text 2>/dev/null)
if [ -z "$PRIV_SUBNET_1" ] || [ "$PRIV_SUBNET_1" == "None" ]; then
    if echo "$VPC_CIDR_BLOCK" | grep -q "^10\.0\.0\.0/16$"; then
        PRIV_SUBNET_1=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.10.0/24 --availability-zone $AZ1 --region $REGION --query 'Subnet.SubnetId' --output text 2>&1)
        if echo "$PRIV_SUBNET_1" | grep -q "error\|Error\|InvalidCidrBlock"; then
            echo "⚠️  Private subnet creation failed, using public subnet for private resources"
            PRIV_SUBNET_1=$PUB_SUBNET_1
        else
            aws ec2 create-tags --resources $PRIV_SUBNET_1 --tags Key=Name,Value=${PROJECT_NAME}-private-1a --region $REGION
        fi
    else
        echo "   Using public subnet for private resources (no dedicated private subnet)"
        PRIV_SUBNET_1=$PUB_SUBNET_1
    fi
fi

PRIV_SUBNET_2=$(aws ec2 describe-subnets --filters "Name=tag:Name,Values=${PROJECT_NAME}-private-1b" --region $REGION --query 'Subnets[0].SubnetId' --output text 2>/dev/null)
if [ -z "$PRIV_SUBNET_2" ] || [ "$PRIV_SUBNET_2" == "None" ]; then
    if echo "$VPC_CIDR_BLOCK" | grep -q "^10\.0\.0\.0/16$"; then
        PRIV_SUBNET_2=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.11.0/24 --availability-zone $AZ2 --region $REGION --query 'Subnet.SubnetId' --output text 2>&1)
        if echo "$PRIV_SUBNET_2" | grep -q "error\|Error\|InvalidCidrBlock"; then
            echo "⚠️  Private subnet creation failed, using public subnet for private resources"
            PRIV_SUBNET_2=$PUB_SUBNET_2
        else
            aws ec2 create-tags --resources $PRIV_SUBNET_2 --tags Key=Name,Value=${PROJECT_NAME}-private-1b --region $REGION
        fi
    else
        echo "   Using public subnet for private resources (no dedicated private subnet)"
        PRIV_SUBNET_2=$PUB_SUBNET_2
    fi
fi

# Create or get Elastic IP and NAT Gateway (optional if using public subnets)
EIP_ALLOC=$(aws ec2 describe-addresses --filters "Name=tag:Name,Values=${PROJECT_NAME}-nat-eip" --region $REGION --query 'Addresses[0].AllocationId' --output text 2>/dev/null)
if [ -z "$EIP_ALLOC" ] || [ "$EIP_ALLOC" == "None" ]; then
    EIP_ALLOC=$(aws ec2 allocate-address --domain vpc --region $REGION --query 'AllocationId' --output text 2>&1)
    if echo "$EIP_ALLOC" | grep -q "AddressLimitExceeded"; then
        echo "⚠️  Elastic IP limit exceeded. Skipping NAT Gateway (using public subnets only)"
        EIP_ALLOC=""
        NAT_GW_ID=""
    else
        aws ec2 create-tags --resources $EIP_ALLOC --tags Key=Name,Value=${PROJECT_NAME}-nat-eip --region $REGION
    fi
fi

NAT_GW_ID=$(aws ec2 describe-nat-gateways --filter "Name=tag:Name,Values=${PROJECT_NAME}-nat" --region $REGION --query 'NatGateways[0].NatGatewayId' --output text 2>/dev/null)
if [ -z "$NAT_GW_ID" ] || [ "$NAT_GW_ID" == "None" ]; then
    if [ ! -z "$EIP_ALLOC" ]; then
        NAT_GW_ID=$(aws ec2 create-nat-gateway --subnet-id $PUB_SUBNET_1 --allocation-id $EIP_ALLOC --region $REGION --query 'NatGateway.NatGatewayId' --output text)
        aws ec2 create-tags --resources $NAT_GW_ID --tags Key=Name,Value=${PROJECT_NAME}-nat --region $REGION
        echo "⏳ Waiting for NAT Gateway..."
        aws ec2 wait nat-gateway-available --nat-gateway-ids $NAT_GW_ID --region $REGION
    else
        echo "⚠️  Skipping NAT Gateway creation (no Elastic IP available)"
    fi
fi

# Create or get route tables
PUB_RT=$(aws ec2 describe-route-tables --filters "Name=tag:Name,Values=${PROJECT_NAME}-public-rt" --region $REGION --query 'RouteTables[0].RouteTableId' --output text 2>/dev/null)
if [ -z "$PUB_RT" ] || [ "$PUB_RT" == "None" ]; then
    PUB_RT=$(aws ec2 create-route-table --vpc-id $VPC_ID --region $REGION --query 'RouteTable.RouteTableId' --output text)
    aws ec2 create-tags --resources $PUB_RT --tags Key=Name,Value=${PROJECT_NAME}-public-rt --region $REGION
    aws ec2 create-route --route-table-id $PUB_RT --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW_ID --region $REGION
fi
aws ec2 associate-route-table --subnet-id $PUB_SUBNET_1 --route-table-id $PUB_RT --region $REGION 2>/dev/null || true
aws ec2 associate-route-table --subnet-id $PUB_SUBNET_2 --route-table-id $PUB_RT --region $REGION 2>/dev/null || true

PRIV_RT=$(aws ec2 describe-route-tables --filters "Name=tag:Name,Values=${PROJECT_NAME}-private-rt" --region $REGION --query 'RouteTables[0].RouteTableId' --output text 2>/dev/null)
if [ -z "$PRIV_RT" ] || [ "$PRIV_RT" == "None" ]; then
    PRIV_RT=$(aws ec2 create-route-table --vpc-id $VPC_ID --region $REGION --query 'RouteTable.RouteTableId' --output text)
    aws ec2 create-tags --resources $PRIV_RT --tags Key=Name,Value=${PROJECT_NAME}-private-rt --region $REGION
    if [ ! -z "$NAT_GW_ID" ] && [ "$NAT_GW_ID" != "None" ]; then
        aws ec2 create-route --route-table-id $PRIV_RT --destination-cidr-block 0.0.0.0/0 --nat-gateway-id $NAT_GW_ID --region $REGION 2>/dev/null || true
    else
        echo "⚠️  Private route table created without NAT Gateway route (using public subnets)"
    fi
fi
aws ec2 associate-route-table --subnet-id $PRIV_SUBNET_1 --route-table-id $PRIV_RT --region $REGION 2>/dev/null || true
aws ec2 associate-route-table --subnet-id $PRIV_SUBNET_2 --route-table-id $PRIV_RT --region $REGION 2>/dev/null || true

# Create or get security groups
ALB_SG=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=${PROJECT_NAME}-alb-sg" --region $REGION --query 'SecurityGroups[0].GroupId' --output text 2>/dev/null)
if [ -z "$ALB_SG" ] || [ "$ALB_SG" == "None" ]; then
    ALB_SG=$(aws ec2 create-security-group --group-name ${PROJECT_NAME}-alb-sg --description "ALB SG" --vpc-id $VPC_ID --region $REGION --query 'GroupId' --output text)
fi
aws ec2 authorize-security-group-ingress --group-id $ALB_SG --protocol tcp --port 80 --cidr 0.0.0.0/0 --region $REGION 2>/dev/null || true
aws ec2 authorize-security-group-ingress --group-id $ALB_SG --protocol tcp --port 443 --cidr 0.0.0.0/0 --region $REGION 2>/dev/null || true

API_SG=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=${PROJECT_NAME}-api-sg" --region $REGION --query 'SecurityGroups[0].GroupId' --output text 2>/dev/null)
if [ -z "$API_SG" ] || [ "$API_SG" == "None" ]; then
    API_SG=$(aws ec2 create-security-group --group-name ${PROJECT_NAME}-api-sg --description "API SG" --vpc-id $VPC_ID --region $REGION --query 'GroupId' --output text)
fi

WORKER_SG=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=${PROJECT_NAME}-worker-sg" --region $REGION --query 'SecurityGroups[0].GroupId' --output text 2>/dev/null)
if [ -z "$WORKER_SG" ] || [ "$WORKER_SG" == "None" ]; then
    WORKER_SG=$(aws ec2 create-security-group --group-name ${PROJECT_NAME}-worker-sg --description "Worker SG" --vpc-id $VPC_ID --region $REGION --query 'GroupId' --output text)
fi

DB_SG=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=${PROJECT_NAME}-db-sg" --region $REGION --query 'SecurityGroups[0].GroupId' --output text 2>/dev/null)
if [ -z "$DB_SG" ] || [ "$DB_SG" == "None" ]; then
    DB_SG=$(aws ec2 create-security-group --group-name ${PROJECT_NAME}-db-sg --description "DB SG" --vpc-id $VPC_ID --region $REGION --query 'GroupId' --output text)
fi

REDIS_SG=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=${PROJECT_NAME}-redis-sg" --region $REGION --query 'SecurityGroups[0].GroupId' --output text 2>/dev/null)
if [ -z "$REDIS_SG" ] || [ "$REDIS_SG" == "None" ]; then
    REDIS_SG=$(aws ec2 create-security-group --group-name ${PROJECT_NAME}-redis-sg --description "Redis SG" --vpc-id $VPC_ID --region $REGION --query 'GroupId' --output text)
fi

# Configure security group rules
aws ec2 authorize-security-group-ingress --group-id $API_SG --protocol tcp --port 8000 --source-group $ALB_SG --region $REGION 2>/dev/null || true
aws ec2 authorize-security-group-ingress --group-id $REDIS_SG --protocol tcp --port 6379 --source-group $API_SG --region $REGION 2>/dev/null || true
aws ec2 authorize-security-group-ingress --group-id $REDIS_SG --protocol tcp --port 6379 --source-group $WORKER_SG --region $REGION 2>/dev/null || true
aws ec2 authorize-security-group-ingress --group-id $DB_SG --protocol tcp --port 5432 --source-group $API_SG --region $REGION 2>/dev/null || true
aws ec2 authorize-security-group-ingress --group-id $DB_SG --protocol tcp --port 5432 --source-group $WORKER_SG --region $REGION 2>/dev/null || true

# Save configuration
cat > aws_config.env << EOF
export AWS_REGION=$REGION
export VPC_ID=$VPC_ID
export IGW_ID=$IGW_ID
export NAT_GW_ID=$NAT_GW_ID
export PUB_SUBNET_1=$PUB_SUBNET_1
export PUB_SUBNET_2=$PUB_SUBNET_2
export PRIV_SUBNET_1=$PRIV_SUBNET_1
export PRIV_SUBNET_2=$PRIV_SUBNET_2
export ALB_SG=$ALB_SG
export API_SG=$API_SG
export WORKER_SG=$WORKER_SG
export DB_SG=$DB_SG
export REDIS_SG=$REDIS_SG
export PROJECT_NAME=$PROJECT_NAME
EOF

echo "✅ Infrastructure created"
