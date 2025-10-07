#!/bin/bash
#
# Frontend Testing Script using Playwright
#
# This script runs browser-based tests for the Simple Kanban Board frontend.
# It tests UI interactions, modal functionality, and user workflows.
#
# Usage:
#   ./scripts/test-frontend.sh                 # Run all frontend tests
#   ./scripts/test-frontend.sh --headed        # Run with visible browser
#   ./scripts/test-frontend.sh --smoke         # Run only smoke tests
#   ./scripts/test-frontend.sh --modal         # Run only modal tests
#   ./scripts/test-frontend.sh --debug         # Run with debugging enabled

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FRONTEND_TEST_DIR="$PROJECT_ROOT/tests/frontend"
NAMESPACE="apps-dev"

# Function to get the service URL dynamically
get_service_url() {
    # Try to get URL from environment variable first
    if [ -n "$BASE_URL" ]; then
        echo "$BASE_URL"
        return
    fi
    
    # Try to get from Kubernetes ingress
    local ingress_host=$(kubectl get ingress simple-kanban-dev -n "$NAMESPACE" -o jsonpath='{.spec.rules[0].host}' 2>/dev/null)
    if [ -n "$ingress_host" ]; then
        echo "https://$ingress_host"
        return
    fi
    
    # Fallback to production URL
    echo "https://kanban.stormpath.dev"
}

export BASE_URL=$(get_service_url)

# Get test credentials from Kubernetes secret if available
if kubectl get secret simple-kanban-test-api-key -n "$NAMESPACE" >/dev/null 2>&1; then
    export TEST_USERNAME="${TEST_USERNAME:-testuser}"
    export TEST_PASSWORD="${TEST_PASSWORD:-TestPassword123!}"
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🎭 Simple Kanban Frontend Testing Suite${NC}"
echo "=============================================="
echo "Base URL: $BASE_URL"
echo "Test Directory: $FRONTEND_TEST_DIR"
echo ""

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo -e "${RED}❌ Poetry is not installed${NC}"
    echo "Please install Poetry: curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

# Navigate to frontend test directory
cd "$FRONTEND_TEST_DIR"

# Install dependencies if needed
if ! poetry run python -c "import playwright" 2>/dev/null; then
    echo -e "${YELLOW}📦 Installing frontend test dependencies with Poetry...${NC}"
    poetry install
    
    echo -e "${YELLOW}🎭 Installing Playwright browsers...${NC}"
    poetry run playwright install chromium
fi

# Parse command line arguments
PYTEST_ARGS=""
BROWSER_ARGS="--browser chromium"
HEADED_MODE=""
TEST_FILTER=""

for arg in "$@"; do
    case $arg in
        --headed)
            HEADED_MODE="--headed"
            shift
            ;;
        --smoke)
            TEST_FILTER="-m smoke"
            shift
            ;;
        --modal)
            TEST_FILTER="-m modal"
            shift
            ;;
        --critical)
            TEST_FILTER="-m critical"
            shift
            ;;
        --debug)
            PYTEST_ARGS="$PYTEST_ARGS --pdb -s"
            HEADED_MODE="--headed"
            BROWSER_ARGS="$BROWSER_ARGS --slowmo 1000"
            shift
            ;;
        --verbose)
            PYTEST_ARGS="$PYTEST_ARGS -vv"
            shift
            ;;
        *)
            # Pass through other arguments
            PYTEST_ARGS="$PYTEST_ARGS $arg"
            shift
            ;;
    esac
done

# Run tests
echo -e "${BLUE}🚀 Running Frontend Tests${NC}"
echo "Browser: chromium (headless: $([ -z "$HEADED_MODE" ] && echo 'yes' || echo 'no'))"
echo "Test Filter: ${TEST_FILTER:-all tests}"
echo ""

# Run pytest with playwright using Poetry
if poetry run pytest $BROWSER_ARGS $HEADED_MODE $TEST_FILTER $PYTEST_ARGS; then
    echo ""
    echo -e "${GREEN}✅ All frontend tests passed!${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}❌ Some frontend tests failed${NC}"
    exit 1
fi
