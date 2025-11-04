#!/bin/bash
# Test runner script for backend tests

echo "Running Backend Tests..."
echo "========================"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Check if pytest-cov is installed
if python -c "import pytest_cov" 2>/dev/null; then
    echo "Running tests with coverage..."
    pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html
    echo ""
    echo "Test coverage report generated in htmlcov/index.html"
else
    echo "pytest-cov not installed. Running tests without coverage..."
    echo "Install with: pip install pytest-cov"
    pytest tests/ -v
fi

