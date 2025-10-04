#!/bin/bash
"""
Post-Deploy Test Hook for Skaffold

This script is designed to be called by Skaffold after deployment.
It waits for the deployment to be ready and then runs the test battery.

Usage:
  ./scripts/post-deploy-test.sh [environment] [test-mode] [fail-mode]
  
Arguments:
  environment: dev, prod (default: dev)
  test-mode: quick, full (default: full)
  fail-mode: hard, soft (default: hard for prod, soft for dev)
  
Fail Modes:
  hard: Exit with error code if tests fail (blocks deployment)
  soft: Report failures but exit with success (allows deployment)
"""

set -e

# Configuration
ENVIRONMENT=${1:-dev}
TEST_MODE=${2:-full}
FAIL_MODE=${3:-""}
NAMESPACE="apps-${ENVIRONMENT}"
DEPLOYMENT_NAME="simple-kanban-${ENVIRONMENT}"

# Set default fail mode based on environment
if [ -z "$FAIL_MODE" ]; then
    if [ "$ENVIRONMENT" = "prod" ]; then
        FAIL_MODE="hard"
    else
        FAIL_MODE="soft"
    fi
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[POST-DEPLOY]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[POST-DEPLOY]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[POST-DEPLOY]${NC} $1"
}

log_error() {
    echo -e "${RED}[POST-DEPLOY]${NC} $1"
}

log_info "Starting post-deploy validation for environment: $ENVIRONMENT"
log_info "Test mode: $TEST_MODE"
log_info "Fail mode: $FAIL_MODE"

# Wait for deployment to be ready
log_info "Waiting for deployment to be ready..."
if kubectl wait --for=condition=available --timeout=300s deployment/$DEPLOYMENT_NAME -n $NAMESPACE; then
    log_success "Deployment is ready"
else
    log_error "Deployment failed to become ready within 5 minutes"
    exit 1
fi

# Additional wait for application startup
log_info "Waiting additional 30 seconds for application startup..."
sleep 30

# Check if test script exists
TEST_SCRIPT="./scripts/test-all.sh"
if [ ! -f "$TEST_SCRIPT" ]; then
    log_error "Test script not found: $TEST_SCRIPT"
    exit 1
fi

# Make script executable
chmod +x "$TEST_SCRIPT"

# Run tests based on mode
log_info "Running test battery in $TEST_MODE mode..."
if [ "$TEST_MODE" = "quick" ]; then
    TEST_ARGS="--quick"
elif [ "$TEST_MODE" = "full" ]; then
    TEST_ARGS=""
else
    log_warning "Unknown test mode '$TEST_MODE', defaulting to quick"
    TEST_ARGS="--quick"
fi

# Execute tests
TEST_EXIT_CODE=0
if "$TEST_SCRIPT" $TEST_ARGS; then
    log_success "All tests passed! Deployment validation successful."
    
    # Optional: Send notification (uncomment if you have notification setup)
    # curl -X POST "https://hooks.slack.com/..." -d "{\"text\":\"✅ $DEPLOYMENT_NAME deployed and tested successfully\"}"
    
else
    TEST_EXIT_CODE=$?
    log_error "Tests failed! Some functionality may be broken."
    
    # Show recent logs for debugging
    log_info "Recent application logs:"
    kubectl logs -n $NAMESPACE deployment/$DEPLOYMENT_NAME --tail=20 || true
fi

# Handle failure based on fail mode
if [ $TEST_EXIT_CODE -ne 0 ]; then
    if [ "$FAIL_MODE" = "soft" ]; then
        log_warning "SOFT FAIL MODE: Tests failed but allowing deployment to continue"
        log_warning "⚠️  Development can continue, but some features may be broken"
        log_info "💡 Check test-results.json for detailed failure information"
        
        # Optional: Send warning notification
        # curl -X POST "https://hooks.slack.com/..." -d "{\"text\":\"⚠️ $DEPLOYMENT_NAME deployed with test failures (soft mode)\"}"
        
        exit 0  # Exit success to allow deployment
    else
        log_error "HARD FAIL MODE: Tests failed, blocking deployment"
        log_error "❌ Deployment validation failed - fix issues before deploying"
        
        # Optional: Send failure notification
        # curl -X POST "https://hooks.slack.com/..." -d "{\"text\":\"❌ $DEPLOYMENT_NAME deployment blocked by test failures\"}"
        
        exit 1  # Exit failure to block deployment
    fi
else
    exit 0  # All tests passed
fi
