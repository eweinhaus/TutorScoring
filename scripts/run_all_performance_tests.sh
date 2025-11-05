#!/bin/bash
# Run all performance tests automatically

set -e

echo "=========================================="
echo "Performance Testing Suite"
echo "=========================================="
echo ""

# Get API key from environment
API_KEY=$(cd backend && source venv/bin/activate && python -c "from dotenv import load_dotenv; import os; load_dotenv('.env'); print(os.getenv('API_KEY', ''))")

if [ -z "$API_KEY" ]; then
    echo "Error: API_KEY not found in backend/.env"
    exit 1
fi

API_URL="http://localhost:8001"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_DIR="performance_results_${TIMESTAMP}"
mkdir -p "$RESULTS_DIR"

echo "API URL: $API_URL"
echo "Results Directory: $RESULTS_DIR"
echo ""

# Activate virtual environment
source backend/venv/bin/activate

# Phase 1: Small Load Test (100 sessions)
echo "=========================================="
echo "Phase 1: Small Load Test (100 sessions)"
echo "=========================================="
python scripts/load_test/session_load.py \
    --api-url "$API_URL" \
    --api-key "$API_KEY" \
    --sessions 100 \
    --rate 125 \
    --output "$RESULTS_DIR/load_test_100.json" || echo "Load test failed (may be expected if services not running)"

echo ""

# Phase 2: API Performance Test
echo "=========================================="
echo "Phase 2: API Performance Test"
echo "=========================================="

# Get a tutor ID
TUTOR_ID=$(python scripts/load_test/get_tutor_ids.py --limit 1 2>&1 | grep -oE '[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}' | head -1)

if [ -z "$TUTOR_ID" ]; then
    echo "Warning: Could not get tutor ID, skipping API test"
else
    python scripts/performance_test/api_performance.py \
        --api-url "$API_URL" \
        --api-key "$API_KEY" \
        --requests 500 \
        --concurrency 25 \
        --tutor-id "$TUTOR_ID" \
        --output "$RESULTS_DIR/api_performance.json" || echo "API performance test failed"
fi

echo ""

# Phase 3: Database Performance Test
echo "=========================================="
echo "Phase 3: Database Performance Test"
echo "=========================================="
python scripts/performance_test/database_performance.py \
    --output "$RESULTS_DIR/database_performance.json" || echo "Database performance test failed"

echo ""

# Phase 4: Frontend Performance Test (if frontend is running)
echo "=========================================="
echo "Phase 4: Frontend Performance Test"
echo "=========================================="
echo "Note: Requires frontend to be running on http://localhost:4173"
echo "      Install Lighthouse: npm install -g lighthouse"
echo ""

if command -v lighthouse &> /dev/null; then
    python scripts/performance_test/frontend_performance.py \
        --url "http://localhost:4173" \
        --output "$RESULTS_DIR/frontend_performance.json" || echo "Frontend performance test failed (frontend may not be running)"
else
    echo "Lighthouse not installed. Skipping frontend test."
    echo "Install with: npm install -g lighthouse"
fi

echo ""

# Summary
echo "=========================================="
echo "Testing Complete"
echo "=========================================="
echo "Results saved to: $RESULTS_DIR"
echo ""
echo "Files generated:"
ls -lh "$RESULTS_DIR" | tail -n +2 | awk '{print "  " $9 " (" $5 ")"}'
echo ""

