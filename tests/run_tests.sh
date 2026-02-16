#!/bin/bash
# Test runner script for ComfyUI-Docker test suite

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default options
TEST_MARKER=""
COVERAGE=true
VERBOSE=false
PARALLEL=false
REPORT_DIR="test-reports"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--marker)
            TEST_MARKER="-m $2"
            shift 2
            ;;
        --no-coverage)
            COVERAGE=false
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -p|--parallel)
            PARALLEL=true
            shift
            ;;
        -r|--report-dir)
            REPORT_DIR="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: run_tests.sh [options]"
            echo ""
            echo "Options:"
            echo "  -m, --marker MARKER    Run tests with specific marker (unit, integration, e2e, performance)"
            echo "  --no-coverage          Skip coverage reporting"
            echo "  -v, --verbose          Verbose output"
            echo "  -p, --parallel         Run tests in parallel"
            echo "  -r, --report-dir DIR   Report directory (default: test-reports)"
            echo "  -h, --help             Show this help message"
            echo ""
            echo "Examples:"
            echo "  run_tests.sh -m unit"
            echo "  run_tests.sh -m integration --no-coverage"
            echo "  run_tests.sh -v --parallel"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Create report directory
mkdir -p "$REPORT_DIR"

# Build pytest command
PYTEST_CMD="pytest"

# Add marker if specified
if [ -n "$TEST_MARKER" ]; then
    PYTEST_CMD="$PYTEST_CMD $TEST_MARKER"
fi

# Add coverage if requested
if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=scripts --cov=app --cov-report=html:$REPORT_DIR/htmlcov --cov-report=xml:$REPORT_DIR/coverage.xml --cov-report=term-missing"
fi

# Add verbose if requested
if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -v -s"
fi

# Add parallel if requested
if [ "$PARALLEL" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -n auto"
fi

# Add other options
PYTEST_CMD="$PYTEST_CMD --timeout=60 --strict-markers --tb=short -ra"

echo -e "${GREEN}Running:${NC} $PYTEST_CMD"
echo ""

# Run tests
if eval $PYTEST_CMD; then
    echo ""
    echo -e "${GREEN}✓ All tests passed!${NC}"

    if [ "$COVERAGE" = true ]; then
        echo ""
        echo -e "${GREEN}Coverage reports generated in:${NC}"
        echo "  HTML: $REPORT_DIR/htmlcov/index.html"
        echo "  XML:  $REPORT_DIR/coverage.xml"
    fi

    exit 0
else
    echo ""
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
