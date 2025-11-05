#!/bin/bash
# Interactive AWS Credentials Setup

export PATH="/opt/homebrew/bin:$PATH"

echo "🔑 AWS Credentials Setup"
echo "========================"
echo ""

# Check if already configured
if aws sts get-caller-identity &>/dev/null; then
    echo "✅ AWS already configured!"
    aws sts get-caller-identity
    exit 0
fi

echo "To get your AWS credentials:"
echo ""
echo "1. Go to: https://console.aws.amazon.com/iam/home#/security_credentials"
echo "2. Sign in with: etweinhaus@gmail.com"
echo "3. Click 'Create access key'"
echo "4. Copy your Access Key ID and Secret Access Key"
echo ""

read -p "Do you have your AWS Access Key ID ready? (y/n): " READY

if [ "$READY" != "y" ]; then
    echo ""
    echo "Please get your credentials first, then run this script again."
    echo "Or run: ./get_aws_credentials.sh for detailed instructions"
    exit 1
fi

echo ""
echo "Enter your AWS credentials:"
read -p "AWS Access Key ID: " AWS_ACCESS_KEY_ID
read -sp "AWS Secret Access Key: " AWS_SECRET_ACCESS_KEY
echo ""

read -p "AWS Region (default: us-east-1): " AWS_REGION
AWS_REGION="${AWS_REGION:-us-east-1}"

echo ""
echo "Configuring AWS CLI..."

# Configure AWS CLI non-interactively
mkdir -p ~/.aws
cat > ~/.aws/credentials << EOF
[default]
aws_access_key_id = ${AWS_ACCESS_KEY_ID}
aws_secret_access_key = ${AWS_SECRET_ACCESS_KEY}
EOF

cat > ~/.aws/config << EOF
[default]
region = ${AWS_REGION}
output = json
EOF

# Test configuration
echo ""
echo "Testing AWS configuration..."
if aws sts get-caller-identity &>/dev/null; then
    echo "✅ AWS credentials configured successfully!"
    aws sts get-caller-identity
    echo ""
    echo "You can now run: ./auto_deploy.sh"
else
    echo "❌ Configuration failed. Please check your credentials."
    exit 1
fi

