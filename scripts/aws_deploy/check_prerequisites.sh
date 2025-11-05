#!/bin/bash
export PATH="/opt/homebrew/bin:$PATH"
# Prerequisites Check Script

set -e

# Add Homebrew to PATH
export PATH="/opt/homebrew/bin:$PATH"

echo "🔍 Checking Prerequisites..."
echo ""

ERRORS=0

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Installing..."
    brew install awscli
    export PATH="/opt/homebrew/bin:$PATH"
fi

if command -v aws &> /dev/null; then
    AWS_VERSION=$(aws --version)
    echo "✅ AWS CLI: $AWS_VERSION"
else
    echo "❌ AWS CLI installation failed"
    ERRORS=$((ERRORS + 1))
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured."
    echo ""
    echo "📝 To configure AWS credentials, you have two options:"
    echo ""
    echo "Option 1: Run 'aws configure' and enter:"
    echo "   - AWS Access Key ID"
    echo "   - AWS Secret Access Key"  
    echo "   - Default region (us-east-1)"
    echo "   - Default output format (json)"
    echo ""
    echo "Option 2: Set environment variables:"
    echo "   export AWS_ACCESS_KEY_ID=your_key"
    echo "   export AWS_SECRET_ACCESS_KEY=your_secret"
    echo "   export AWS_DEFAULT_REGION=us-east-1"
    echo ""
    echo "Get your credentials from:"
    echo "   https://console.aws.amazon.com/iam/home#/security_credentials"
    echo ""
    ERRORS=$((ERRORS + 1))
else
    AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
    AWS_USER=$(aws sts get-caller-identity --query Arn --output text)
    echo "✅ AWS credentials configured"
    echo "   Account: $AWS_ACCOUNT"
    echo "   User: $AWS_USER"
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "⚠️  Docker not found. Docker is required for building and pushing images."
    echo "   You can install it with: brew install --cask docker-desktop"
    echo "   Or skip Docker step and use pre-built images if available."
    echo "   Note: Docker Desktop requires manual start after installation."
    ERRORS=$((ERRORS + 1))
else
    DOCKER_VERSION=$(docker --version)
    echo "✅ Docker: $DOCKER_VERSION"
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        echo "⚠️  Docker daemon not running. Start Docker Desktop."
        echo "   Run: open -a Docker"
        echo "   Wait for Docker to start, then run this script again."
        ERRORS=$((ERRORS + 1))
    else
        echo "✅ Docker daemon is running"
    fi
fi

# Check jq (optional but recommended)
if ! command -v jq &> /dev/null; then
    echo "⚠️  jq not found (optional but recommended for JSON parsing)"
    echo "   Install: brew install jq (macOS) or apt-get install jq (Linux)"
else
    echo "✅ jq installed"
fi

# Check Node.js (for frontend build)
if ! command -v node &> /dev/null; then
    echo "⚠️  Node.js not found (required for frontend deployment)"
    ERRORS=$((ERRORS + 1))
else
    NODE_VERSION=$(node --version)
    echo "✅ Node.js: $NODE_VERSION"
fi

# Check npm
if ! command -v npm &> /dev/null; then
    echo "⚠️  npm not found (required for frontend deployment)"
    ERRORS=$((ERRORS + 1))
else
    NPM_VERSION=$(npm --version)
    echo "✅ npm: $NPM_VERSION"
fi

echo ""

if [ $ERRORS -gt 0 ]; then
    echo "❌ Prerequisites check failed. Please fix the errors above."
    exit 1
else
    echo "✅ All prerequisites met!"
    exit 0
fi

