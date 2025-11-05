#!/bin/bash
export PATH="/opt/homebrew/bin:$PATH"
# Check for Docker alternatives or workarounds

echo "🔍 Checking Docker alternatives..."

# Check if Docker is available
if command -v docker &>/dev/null && docker info &>/dev/null; then
    echo "✅ Docker is available and running"
    exit 0
fi

# Check if we can use existing images
echo "⚠️  Docker not available"
echo ""
echo "Options:"
echo "1. Install Docker Desktop manually: brew install --cask docker-desktop"
echo "2. Start Docker Desktop if already installed"
echo "3. Use pre-built images (if available)"
echo ""
echo "For now, deployment will pause at ECR step until Docker is available."
exit 1
