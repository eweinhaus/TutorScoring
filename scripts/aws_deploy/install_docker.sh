#!/bin/bash
# Docker Installation Script
export PATH="/opt/homebrew/bin:$PATH"

echo "🐳 Installing Docker Desktop..."
echo ""

if command -v docker &>/dev/null && docker info &>/dev/null; then
    echo "✅ Docker is already installed and running"
    docker --version
    exit 0
fi

# Check if Docker Desktop app exists
if [ -d "/Applications/Docker.app" ]; then
    echo "✅ Docker Desktop is installed"
    echo "Starting Docker Desktop..."
    open -a Docker
    echo "⏳ Waiting for Docker to start (this may take 1-2 minutes)..."
    
    # Wait for Docker to be ready
    for i in {1..60}; do
        if docker info &>/dev/null; then
            echo "✅ Docker is now running!"
            docker --version
            exit 0
        fi
        sleep 2
        echo -n "."
    done
    echo ""
    echo "⚠️  Docker Desktop is starting but not ready yet."
    echo "   Please wait for Docker Desktop to fully start (check system tray)"
    echo "   Then run: docker info"
    exit 1
fi

echo "Installing Docker Desktop via Homebrew..."
echo "Note: This may require your password for sudo"
echo ""

# Try to install - may require sudo password
brew install --cask docker-desktop

if [ -d "/Applications/Docker.app" ]; then
    echo "✅ Docker Desktop installed"
    echo "Starting Docker Desktop..."
    open -a Docker
    echo ""
    echo "⏳ Docker Desktop is starting..."
    echo "   Please wait 1-2 minutes for Docker to be ready"
    echo "   You'll see Docker icon in your menu bar when ready"
    echo ""
    echo "Then run: docker info"
else
    echo "❌ Docker installation failed"
    echo "   You may need to install manually from: https://www.docker.com/products/docker-desktop"
    exit 1
fi
