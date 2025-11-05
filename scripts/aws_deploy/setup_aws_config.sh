#!/bin/bash
export PATH="/opt/homebrew/bin:$PATH"
# Setup AWS Configuration
export PATH="/opt/homebrew/bin:$PATH"

echo "🔧 Setting up AWS Configuration..."
echo ""

# Check if already configured
if aws sts get-caller-identity &>/dev/null; then
    echo "✅ AWS CLI already configured"
    aws sts get-caller-identity
    exit 0
fi

echo "AWS CLI needs to be configured."
echo "You need:"
echo "  1. AWS Access Key ID"
echo "  2. AWS Secret Access Key"
echo "  3. Default region (us-east-1 recommended)"
echo "  4. Default output format (json recommended)"
echo ""
echo "Get these from: https://console.aws.amazon.com/iam/home#/security_credentials"
echo ""
echo "Run: aws configure"
echo "Or set environment variables:"
echo "  export AWS_ACCESS_KEY_ID=your_key"
echo "  export AWS_SECRET_ACCESS_KEY=your_secret"
echo "  export AWS_DEFAULT_REGION=us-east-1"
