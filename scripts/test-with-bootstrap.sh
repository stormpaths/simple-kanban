#!/bin/bash
# Test Suite with Automatic Bootstrap
#
# This script automatically creates a test environment if needed, then runs the full test suite.
# It handles the case where no API key secret exists by creating one dynamically.
#
# Usage:
#   ./scripts/test-with-bootstrap.sh [test-all.sh arguments]
#   ./scripts/test-with-bootstrap.sh --quick
#   ./scripts/test-with-bootstrap.sh --verbose

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAMESPACE="apps-dev"
SECRET_NAME="simple-kanban-test-api-key"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_failure() {
    echo -e "${RED}❌ $1${NC}"
}

echo -e "${BLUE}🧪 Test Suite with Auto-Bootstrap${NC}"
echo "======================================="

# Check if API key secret exists
log_info "Checking for existing test environment..."

if ! kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" >/dev/null 2>&1; then
    log_info "No test environment found - creating one..."
    
    # Run bootstrap to create test environment
    if [ -f "$SCRIPT_DIR/test-bootstrap.sh" ]; then
        log_info "Running bootstrap script..."
        if "$SCRIPT_DIR/test-bootstrap.sh"; then
            log_success "Test environment created successfully"
        else
            log_failure "Failed to create test environment"
            echo ""
            echo -e "${YELLOW}💡 Troubleshooting:${NC}"
            echo "1. Make sure the application is running"
            echo "2. Check that BASE_URL is correct (default: https://localhost:8000)"
            echo "3. Verify kubectl access to namespace: $NAMESPACE"
            echo ""
            echo -e "${BLUE}Manual bootstrap:${NC}"
            echo "  ./scripts/test-bootstrap.sh"
            exit 1
        fi
    else
        log_failure "Bootstrap script not found: $SCRIPT_DIR/test-bootstrap.sh"
        exit 1
    fi
else
    log_success "Existing test environment found"
fi

# Now run the main test suite with all passed arguments
log_info "Running main test suite..."
echo ""

if "$SCRIPT_DIR/test-all.sh" "$@"; then
    echo ""
    log_success "All tests completed successfully!"
else
    echo ""
    log_failure "Some tests failed"
    exit 1
fi
