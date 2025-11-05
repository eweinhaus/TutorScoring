#!/bin/bash
# Start Here - Complete Setup Guide
export PATH="/opt/homebrew/bin:$PATH"

echo "🚀 AWS Deployment Setup"
echo "======================"
echo ""

# Step 1: AWS Credentials
echo "Step 1/3: AWS Credentials"
echo "------------------------"
if aws sts get-caller-identity &>/dev/null; then
    echo "✅ AWS credentials configured"
    aws sts get-caller-identity
else
    echo "❌ AWS credentials not configured"
    echo ""
    echo "To get your AWS credentials:"
    echo "1. Go to: https://console.aws.amazon.com/iam/home#/security_credentials"
    echo "2. Sign in with: etweinhaus@gmail.com"
    echo "3. Click 'Create access key'"
    echo "4. Copy Access Key ID and Secret Access Key"
    echo ""
    echo "Then run: ./setup_aws_credentials.sh"
    echo ""
    read -p "Press Enter when ready to continue..."
fi

echo ""
echo "Step 2/3: Docker"
echo "---------------"
if command -v docker &>/dev/null && docker info &>/dev/null; then
    echo "✅ Docker is running"
    docker --version
else
    echo "❌ Docker not running"
    echo ""
    echo "Installing/starting Docker..."
    ./install_docker.sh
    echo ""
    read -p "Press Enter when Docker is ready..."
fi

echo ""
echo "Step 3/3: Deploy"
echo "---------------"
echo "Ready to deploy!"
echo ""
read -p "Start deployment now? (y/n): " START

if [ "$START" == "y" ]; then
    ./auto_deploy.sh
else
    echo ""
    echo "When ready, run: ./auto_deploy.sh"
fi
