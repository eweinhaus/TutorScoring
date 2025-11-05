#!/bin/bash
# Non-interactive AWS Configuration Helper
export PATH="/opt/homebrew/bin:$PATH"

echo "🔧 AWS Configuration Helper"
echo ""

# Check if already configured
if aws sts get-caller-identity &>/dev/null; then
    echo "✅ AWS already configured"
    aws sts get-caller-identity
    exit 0
fi

# Check for environment variables
if [ ! -z "$AWS_ACCESS_KEY_ID" ] && [ ! -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "✅ Found AWS credentials in environment variables"
    export AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}"
    aws sts get-caller-identity
    exit 0
fi

# Check for credentials file
if [ -f ~/.aws/credentials ]; then
    echo "✅ Found AWS credentials file"
    export AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}"
    if aws sts get-caller-identity &>/dev/null; then
        aws sts get-caller-identity
        exit 0
    fi
fi

echo "❌ AWS credentials not found"
echo ""
echo "To proceed, you need to:"
echo "1. Get your AWS Access Key ID and Secret Access Key from:"
echo "   https://console.aws.amazon.com/iam/home#/security_credentials"
echo ""
echo "2. Then either:"
echo "   - Run: aws configure"
echo "   - Or set: export AWS_ACCESS_KEY_ID=xxx && export AWS_SECRET_ACCESS_KEY=xxx"
echo ""
exit 1
