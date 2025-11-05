#!/bin/bash
export PATH="/opt/homebrew/bin:$PATH"
# Install Prerequisites Script

set -e

echo "🔧 Installing Prerequisites..."
echo ""

# Check for Homebrew
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Install AWS CLI
if ! command -v aws &> /dev/null; then
    echo "📦 Installing AWS CLI..."
    brew install awscli
else
    echo "✅ AWS CLI already installed"
fi

# Install Docker (via Docker Desktop)
if ! command -v docker &> /dev/null; then
    echo "📦 Installing Docker Desktop..."
    brew install --cask docker
    echo "⚠️  Docker Desktop installed. Please start Docker Desktop application."
    echo "   Open Docker Desktop and wait for it to start, then run this script again."
    exit 1
else
    if ! docker info &> /dev/null; then
        echo "⚠️  Docker is installed but daemon is not running."
        echo "   Please start Docker Desktop and wait for it to be ready."
        exit 1
    else
        echo "✅ Docker is installed and running"
    fi
fi

# Install jq if not present
if ! command -v jq &> /dev/null; then
    echo "📦 Installing jq..."
    brew install jq
else
    echo "✅ jq already installed"
fi

echo ""
echo "✅ All prerequisites installed!"
echo ""
echo "📝 Next step: Configure AWS CLI"
echo "   Run: aws configure"
echo "   Enter your AWS Access Key ID, Secret Access Key, region (us-east-1), and output format (json)"
echo ""
echo "   Then run: ./auto_deploy.sh"

