#!/bin/bash
set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

if [ -d "venv" ]; then
    source venv/bin/activate
fi

TEST_TYPE="${1:-unit}"

case "$TEST_TYPE" in
    unit)
        echo "=== Unit Tests ==="
        python -m pytest tests/unit -v --tb=short
        ;;
    integration)
        echo "=== Integration Tests ==="
        python -m pytest tests/integration -v --tb=short
        ;;
    e2e)
        echo "=== E2E Tests ==="
        python -m pytest tests/e2e -v --tb=short
        ;;
    all)
        echo "=== All Tests ==="
        python -m pytest tests/ -v --tb=short
        ;;
    coverage)
        echo "=== Tests with Coverage ==="
        python -m pytest tests/unit tests/integration --cov=src --cov-report=term-missing --cov-report=html
        ;;
    *)
        echo "Usage: $0 {unit|integration|e2e|all|coverage}"
        exit 1
        ;;
esac
