#!/bin/bash
# Test runner script for AI-LinkMO CLI Demo tests

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}AI-LinkMO CLI Demo Test Suite${NC}"
echo "============================================="
echo ""

# Check if test dependencies are installed
if ! python -c "import pytest" 2>/dev/null; then
    echo -e "${YELLOW}Installing test dependencies...${NC}"
    uv sync --extra test
    echo ""
fi

TIMEOUT="2000"  # Default timeout for tests
# Parse arguments
MODE=${1:-"fast"}

case "$MODE" in
    "fast")
        echo -e "${GREEN}Running fast tests (API mode only)...${NC}"
        uv run pytest lib/test/test_cli_examples.py::test_cli_api_mode -v -m "not slow"
        ;;
    
    "full")
        echo -e "${GREEN}Running full test suite (API + local modes)...${NC}"
        uv run pytest lib/test/test_cli_examples.py -v -s
        ;;
    
    "api")
        echo -e "${GREEN}Running API mode tests...${NC}"
        uv run pytest lib/test/test_cli_examples.py::test_cli_api_mode -v
        ;;
    
    "local")
        echo -e "${GREEN}Running local mode tests...${NC}"
        uv run pytest lib/test/test_cli_examples.py::test_cli_local_mode -v -s
        ;;
    
    "consistency")
        echo -e "${GREEN}Running consistency tests...${NC}"
        uv run pytest lib/test/test_cli_examples.py -v -s -k "consistency"
        ;;
    
    "coverage")
        echo -e "${GREEN}Running tests with coverage...${NC}"
        uv run pytest lib/test/ --cov=lib.cli --cov=lib.api --cov-report=term --cov-report=html
        echo ""
        echo -e "${GREEN}Coverage report generated in htmlcov/index.html${NC}"
        ;;
    
    "ci")
        echo -e "${GREEN}Running CI test suite...${NC}"
        uv run pytest lib/test/test_cli_examples.py::test_cli_api_mode -v --tb=short
        uv run pytest lib/test/test_cli_examples.py -v -k "consistency or health" --tb=short
        ;;
    
    "validate")
        echo -e "${GREEN}Validating handlers against OpenAPI spec...${NC}"
        python lib/test/validate_handlers.py --strict
        ;;
    
    *)
        echo -e "${RED}Unknown mode: $MODE${NC}"
        echo ""
        echo "Usage: ./tests.sh [mode]"
        echo ""
        echo "Modes:"
        echo "  fast        - Run fast tests only (API mode, ~2 min) [default]"
        echo "  full        - Run all tests (API + local modes, shows commands, ~15 min)"
        echo "  api         - Run API mode tests only"
        echo "  local       - Run local mode tests only (shows commands)"
        echo "  consistency - Run consistency tests only (shows commands)"
        echo "  coverage    - Run with coverage report"
        echo "  ci          - Run minimal CI test suite"
        echo "  validate    - Validate handler signatures"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}✓ Tests completed${NC}"
