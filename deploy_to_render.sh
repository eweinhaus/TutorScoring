#!/bin/bash
# Render Deployment Script
# This script helps deploy the TutorScoring application to Render

echo "🚀 TutorScoring Render Deployment"
echo "================================"
echo ""

# Check if Render CLI is available
if ! command -v render &> /dev/null; then
    echo "❌ Render CLI not found. Installing..."
    echo "Please install Render CLI first:"
    echo "  brew install render"
    echo "  OR"
    echo "  npm install -g render-cli"
    echo ""
    echo "Then authenticate:"
    echo "  render login"
    exit 1
fi

echo "✅ Render CLI found"
echo ""

# Check authentication
echo "Checking authentication..."
if ! render whoami &> /dev/null; then
    echo "❌ Not authenticated. Please run: render login"
    exit 1
fi

echo "✅ Authenticated"
echo ""

# Deploy using render.yaml blueprint
echo "📋 Deploying from render.yaml..."
echo "This will create:"
echo "  - PostgreSQL database (tutor-scoring-db)"
echo "  - Redis instance (tutor-scoring-redis)"
echo "  - Backend API (tutor-scoring-api)"
echo "  - Celery Worker (tutor-scoring-worker)"
echo "  - Frontend Static Site (tutor-scoring-frontend)"
echo ""

read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled"
    exit 0
fi

# Deploy blueprint
echo ""
echo "🚀 Starting deployment..."
render blueprint apply render.yaml

echo ""
echo "✅ Deployment initiated!"
echo ""
echo "📝 Next steps:"
echo "1. Go to Render Dashboard: https://dashboard.render.com"
echo "2. Wait for all services to deploy (5-10 minutes)"
echo "3. Set environment variables in each service:"
echo "   - SENDGRID_API_KEY: (your key)"
echo "   - ADMIN_EMAIL: (your email)"
echo "   - SECRET_KEY: 1fGValreU6KyIDH9K7NhjBVThSw-e93hkd9nSIT_Rvg"
echo "   - API_KEY: qfWmQnfRHVHhmVHZ3oZ0gUKeeVLOZOXwovB_PCapnvg"
echo "4. Run migrations: Backend Shell → 'cd backend && alembic upgrade head'"
echo "5. Update frontend VITE_API_URL after backend deploys"
echo ""

