#!/bin/bash
#
# Parallel Test Execution Script
#
# Runs backend and frontend tests simultaneously for faster execution
# and better resource utilization.
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Configuration
WORKERS=${WORKERS:-4}  # Number of parallel frontend workers
BACKEND_LOG="$PROJECT_ROOT/backend-test.log"
FRONTEND_LOG="$PROJECT_ROOT/frontend-test.log"

# Logging functions
log_header() {
    echo -e "\n${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC} ${WHITE}$1${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}\n"
}

log_info() {
    echo -e "${BLUE}ℹ${NC}  $1"
}

log_success() {
    echo -e "${GREEN}✓${NC}  $1"
}

log_error() {
    echo -e "${RED}✗${NC}  $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC}  $1"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up..."
    rm -f "$BACKEND_LOG" "$FRONTEND_LOG"
}

trap cleanup EXIT

# Main execution
START_TIME=$(date +%s)

log_header "PARALLEL TEST EXECUTION"

log_info "Configuration:"
echo "  • Frontend workers: $WORKERS"
echo "  • Backend tests: Running in parallel"
echo "  • Frontend tests: Running in parallel"
echo ""

# Start backend tests in background
log_info "Starting backend tests..."
(
    cd "$PROJECT_ROOT"
    
    # Run backend test scripts
    echo "=== Backend Tests Started ===" > "$BACKEND_LOG"
    echo "Timestamp: $(date)" >> "$BACKEND_LOG"
    echo "" >> "$BACKEND_LOG"
    
    # Health check
    echo "Running health check..." >> "$BACKEND_LOG"
    ./scripts/test-auth-comprehensive.sh >> "$BACKEND_LOG" 2>&1
    BACKEND_EXIT=$?
    
    echo "" >> "$BACKEND_LOG"
    echo "=== Backend Tests Completed ===" >> "$BACKEND_LOG"
    echo "Exit code: $BACKEND_EXIT" >> "$BACKEND_LOG"
    
    exit $BACKEND_EXIT
) &
BACKEND_PID=$!

# Start frontend tests in background
log_info "Starting frontend tests (parallel execution)..."
(
    cd "$PROJECT_ROOT/tests/frontend"
    
    echo "=== Frontend Tests Started ===" > "$FRONTEND_LOG"
    echo "Timestamp: $(date)" >> "$FRONTEND_LOG"
    echo "Workers: $WORKERS" >> "$FRONTEND_LOG"
    echo "" >> "$FRONTEND_LOG"
    
    # Run frontend tests with pytest-xdist
    docker-compose run --rm frontend-tests \
        pytest -n $WORKERS --dist loadgroup -v \
        >> "$FRONTEND_LOG" 2>&1
    FRONTEND_EXIT=$?
    
    echo "" >> "$FRONTEND_LOG"
    echo "=== Frontend Tests Completed ===" >> "$FRONTEND_LOG"
    echo "Exit code: $FRONTEND_EXIT" >> "$FRONTEND_LOG"
    
    exit $FRONTEND_EXIT
) &
FRONTEND_PID=$!

# Wait for both to complete
log_info "Waiting for tests to complete..."
echo ""

# Monitor progress
BACKEND_DONE=false
FRONTEND_DONE=false

while [ "$BACKEND_DONE" = false ] || [ "$FRONTEND_DONE" = false ]; do
    if [ "$BACKEND_DONE" = false ] && ! kill -0 $BACKEND_PID 2>/dev/null; then
        wait $BACKEND_PID
        BACKEND_EXIT=$?
        BACKEND_DONE=true
        if [ $BACKEND_EXIT -eq 0 ]; then
            log_success "Backend tests completed successfully"
        else
            log_error "Backend tests failed (exit code: $BACKEND_EXIT)"
        fi
    fi
    
    if [ "$FRONTEND_DONE" = false ] && ! kill -0 $FRONTEND_PID 2>/dev/null; then
        wait $FRONTEND_PID
        FRONTEND_EXIT=$?
        FRONTEND_DONE=true
        if [ $FRONTEND_EXIT -eq 0 ]; then
            log_success "Frontend tests completed successfully"
        else
            log_error "Frontend tests failed (exit code: $FRONTEND_EXIT)"
        fi
    fi
    
    sleep 1
done

# Calculate duration
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# Display results
log_header "TEST EXECUTION SUMMARY"

echo -e "${WHITE}Execution Details:${NC}"
echo "  Duration: ${DURATION}s"
echo "  Backend: $([ $BACKEND_EXIT -eq 0 ] && echo -e "${GREEN}PASSED${NC}" || echo -e "${RED}FAILED${NC}")"
echo "  Frontend: $([ $FRONTEND_EXIT -eq 0 ] && echo -e "${GREEN}PASSED${NC}" || echo -e "${RED}FAILED${NC}")"
echo ""

# Show logs if there were failures
if [ $BACKEND_EXIT -ne 0 ]; then
    log_error "Backend test failures detected. Last 20 lines:"
    tail -20 "$BACKEND_LOG"
    echo ""
fi

if [ $FRONTEND_EXIT -ne 0 ]; then
    log_error "Frontend test failures detected. Last 20 lines:"
    tail -20 "$FRONTEND_LOG"
    echo ""
fi

# Overall result
TOTAL_EXIT=$((BACKEND_EXIT + FRONTEND_EXIT))

if [ $TOTAL_EXIT -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║${NC} ${WHITE}🎉 ALL TESTS PASSED! 🎉${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${RED}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║${NC} ${WHITE}💥 SOME TESTS FAILED 💥${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════╝${NC}"
    
    log_info "Full logs available at:"
    echo "  • Backend: $BACKEND_LOG"
    echo "  • Frontend: $FRONTEND_LOG"
    
    exit 1
fi
