#!/bin/bash
#
# Run Frontend Tests in Docker Container
#
# This script runs Playwright tests in a Docker container with all
# browser dependencies pre-installed.
#
# Usage:
#   ./scripts/test-frontend-docker.sh                 # Run all tests
#   ./scripts/test-frontend-docker.sh --modal         # Run only modal tests
#   ./scripts/test-frontend-docker.sh --build         # Rebuild container
#   ./scripts/test-frontend-docker.sh --report        # Generate HTML report
#   ./scripts/test-frontend-docker.sh --shell         # Open shell in container

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

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🐳 Frontend Tests in Docker${NC}"
echo "=============================================="
echo "Base URL: $BASE_URL"
echo "Test Directory: $FRONTEND_TEST_DIR"
echo ""

# Navigate to frontend test directory
cd "$FRONTEND_TEST_DIR"

# Parse command line arguments
MODE="all"
BUILD_FLAG=""

for arg in "$@"; do
    case $arg in
        --build)
            BUILD_FLAG="--build"
            echo -e "${YELLOW}🔨 Rebuilding Docker image...${NC}"
            shift
            ;;
        --modal)
            MODE="modal"
            shift
            ;;
        --report)
            MODE="report"
            shift
            ;;
        --shell)
            MODE="shell"
            shift
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --build    Rebuild Docker image"
            echo "  --modal    Run only modal tests"
            echo "  --report   Generate HTML report"
            echo "  --shell    Open shell in container"
            echo "  --help     Show this help message"
            exit 0
            ;;
    esac
done

# Run appropriate docker-compose service
case $MODE in
    all)
        echo -e "${BLUE}🚀 Running all frontend tests in Docker...${NC}"
        docker-compose run --rm $BUILD_FLAG frontend-tests
        ;;
    modal)
        echo -e "${BLUE}🚀 Running modal tests in Docker...${NC}"
        docker-compose run --rm $BUILD_FLAG modal-tests
        ;;
    report)
        echo -e "${BLUE}🚀 Running tests with HTML report...${NC}"
        docker-compose run --rm $BUILD_FLAG tests-with-report
        if [ -f "test-results/report.html" ]; then
            echo ""
            echo -e "${GREEN}✅ HTML report generated!${NC}"
            echo -e "View at: ${BLUE}$FRONTEND_TEST_DIR/test-results/report.html${NC}"
        fi
        ;;
    shell)
        echo -e "${BLUE}🐚 Opening shell in test container...${NC}"
        docker-compose run --rm $BUILD_FLAG frontend-tests /bin/bash
        ;;
esac

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Docker tests completed successfully!${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}❌ Some Docker tests failed${NC}"
    exit 1
fi
