#!/bin/bash
# Setup script for Matching Service
# Automates directory creation and dependency verification

set -e  # Exit on error

echo "🔧 Setting up Matching Service prerequisites..."

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

echo "📁 Creating directory structure..."

# Create backend/models directory for ML models
mkdir -p "$BACKEND_DIR/models"
echo "  ✓ Created $BACKEND_DIR/models/"

# Create frontend matching components directory
mkdir -p "$FRONTEND_DIR/src/components/matching"
echo "  ✓ Created $FRONTEND_DIR/src/components/matching/"

echo ""
echo "📦 Checking Python dependencies..."

# Check if virtual environment exists
if [ ! -d "$BACKEND_DIR/venv" ]; then
    echo "  ⚠️  Virtual environment not found. Creating one..."
    cd "$BACKEND_DIR"
    python3 -m venv venv
    echo "  ✓ Virtual environment created"
fi

# Activate virtual environment
source "$BACKEND_DIR/venv/bin/activate"

# Check if required packages are installed
echo "  Checking required packages..."
MISSING_PACKAGES=()

check_package() {
    if python3 -c "import $1" 2>/dev/null; then
        echo "    ✓ $1 installed"
    else
        echo "    ✗ $1 missing"
        MISSING_PACKAGES+=("$1")
    fi
}

check_package "xgboost"
check_package "sklearn"
check_package "pandas"
check_package "numpy"
check_package "joblib"
check_package "openai"

if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    echo ""
    echo "  ⚠️  Missing packages detected. Installing..."
    cd "$BACKEND_DIR"
    pip install -r requirements.txt
    echo "  ✓ Dependencies installed"
else
    echo "  ✓ All required packages installed"
fi

echo ""
echo "🔍 Verifying infrastructure..."

# Check PostgreSQL
if command -v pg_isready &> /dev/null; then
    if pg_isready -q; then
        echo "  ✓ PostgreSQL is running"
    else
        echo "  ⚠️  PostgreSQL is not running"
    fi
else
    echo "  ⚠️  pg_isready not found (PostgreSQL tools not in PATH)"
fi

# Check Redis
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo "  ✓ Redis is running"
    else
        echo "  ⚠️  Redis is not running"
    fi
else
    echo "  ⚠️  redis-cli not found (Redis tools not in PATH)"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "  1. Set OPENAI_API_KEY in backend/.env"
echo "  2. Run database migrations: cd backend && alembic upgrade head"
echo "  3. Train model: python scripts/train_match_model.py"
echo "  4. Generate data: python scripts/generate_matching_data.py"


