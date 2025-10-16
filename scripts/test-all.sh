#!/bin/bash
#
# Comprehensive Test Battery for Simple Kanban Board
#
# This script runs all functional and smoke tests to validate the entire application
# after deployment. It provides a unified report of all test results.
#
# Usage:
#   ./scripts/test-all.sh                    # Run all tests
#   ./scripts/test-all.sh --quick            # Skip slow tests
#   ./scripts/test-all.sh --verbose          # Show detailed output
#   ./scripts/test-all.sh --stop-on-fail     # Stop on first failure
#

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
NAMESPACE="${NAMESPACE:-apps-dev}"
SECRET_NAME="simple-kanban-test-api-key"

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

BASE_URL=$(get_service_url)

# Parse command line arguments
QUICK_MODE=false
VERBOSE_MODE=false
STOP_ON_FAIL=false

for arg in "$@"; do
    case $arg in
        --quick)
            QUICK_MODE=true
            shift
            ;;
        --verbose)
            VERBOSE_MODE=true
            shift
            ;;
        --stop-on-fail)
            STOP_ON_FAIL=true
            shift
            ;;
        --help)
            echo "Usage: $0 [--quick] [--verbose] [--stop-on-fail] [--help]"
            echo ""
            echo "Options:"
            echo "  --quick         Skip slow/comprehensive tests"
            echo "  --verbose       Show detailed test output"
            echo "  --stop-on-fail  Stop execution on first test failure"
            echo "  --help          Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $arg"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Test results tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0
TEST_RESULTS=()

# Utility functions
log_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${WHITE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
}

log_test() {
    echo -e "\n${CYAN}🧪 $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_failure() {
    echo -e "${RED}❌ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_skip() {
    echo -e "${YELLOW}⏭️  $1${NC}"
}

# Function to run a test script and capture results
run_test_script() {
    local script_name=$1
    local test_description=$2
    local script_path="$SCRIPT_DIR/$script_name"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    log_test "Running $test_description"
    
    if [ ! -f "$script_path" ]; then
        log_failure "Test script not found: $script_path"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        TEST_RESULTS+=("❌ $test_description - Script not found")
        if [ "$STOP_ON_FAIL" = true ]; then
            exit 1
        fi
        return 1
    fi
    
    # Make script executable if it isn't
    chmod +x "$script_path"
    
    # Run the test script
    local output_file=$(mktemp)
    local start_time=$(date +%s)
    
    if [ "$VERBOSE_MODE" = true ]; then
        echo -e "${PURPLE}Running: $script_path${NC}"
        if "$script_path" 2>&1 | tee "$output_file"; then
            local exit_code=0
        else
            local exit_code=$?
        fi
    else
        if "$script_path" > "$output_file" 2>&1; then
            local exit_code=0
        else
            local exit_code=$?
        fi
    fi
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    if [ $exit_code -eq 0 ]; then
        log_success "$test_description completed successfully (${duration}s)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        TEST_RESULTS+=("✅ $test_description - Passed (${duration}s)")
    else
        log_failure "$test_description failed (exit code: $exit_code)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        TEST_RESULTS+=("❌ $test_description - Failed (${duration}s)")
        
        # Show last few lines of output on failure
        if [ "$VERBOSE_MODE" = false ]; then
            echo -e "${RED}Last 10 lines of output:${NC}"
            tail -10 "$output_file"
        fi
        
        if [ "$STOP_ON_FAIL" = true ]; then
            rm -f "$output_file"
            exit 1
        fi
    fi
    
    rm -f "$output_file"
    return $exit_code
}

# Function to run a quick health check
run_health_check() {
    log_test "Application Health Check"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    local health_response=$(curl -s -w "%{http_code}" "$BASE_URL/health" -o /dev/null)
    
    if [ "$health_response" = "200" ]; then
        log_success "Application is responding (HTTP 200)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        TEST_RESULTS+=("✅ Health Check - Application responding")
    else
        log_failure "Application health check failed (HTTP $health_response)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        TEST_RESULTS+=("❌ Health Check - HTTP $health_response")
        if [ "$STOP_ON_FAIL" = true ]; then
            exit 1
        fi
    fi
}

# Function to verify API key exists (with auto-bootstrap)
verify_api_key() {
    log_test "API Key Verification"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" > /dev/null 2>&1; then
        local api_key=$(kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" -o jsonpath='{.data.api-key}' | base64 -d)
        if [ -n "$api_key" ]; then
            log_success "API key found and accessible"
            PASSED_TESTS=$((PASSED_TESTS + 1))
            TEST_RESULTS+=("✅ API Key Verification - Key accessible")
        else
            log_failure "API key is empty"
            FAILED_TESTS=$((FAILED_TESTS + 1))
            TEST_RESULTS+=("❌ API Key Verification - Empty key")
        fi
    else
        log_info "API key secret not found - attempting to bootstrap test environment..."
        
        # Try to run bootstrap script
        if [ -f "$SCRIPT_DIR/test-bootstrap.sh" ]; then
            log_info "Running bootstrap script to create test environment..."
            if NAMESPACE="$NAMESPACE" BASE_URL="$BASE_URL" "$SCRIPT_DIR/test-bootstrap.sh" > /dev/null 2>&1; then
                log_success "Bootstrap completed - test environment created"
                # Verify the key was created
                local api_key=$(kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" -o jsonpath='{.data.api-key}' | base64 -d 2>/dev/null)
                if [ -n "$api_key" ]; then
                    log_success "API key now available after bootstrap"
                    PASSED_TESTS=$((PASSED_TESTS + 1))
                    TEST_RESULTS+=("✅ API Key Verification - Key accessible")
                else
                    log_failure "Bootstrap completed but API key still not accessible"
                    FAILED_TESTS=$((FAILED_TESTS + 1))
                    TEST_RESULTS+=("❌ API Key Verification - Bootstrap failed")
                fi
            else
                log_failure "Bootstrap script failed"
                FAILED_TESTS=$((FAILED_TESTS + 1))
                TEST_RESULTS+=("❌ API Key Verification - Bootstrap failed")
                if [ "$STOP_ON_FAIL" = true ]; then
                    exit 1
                fi
            fi
        else
            log_failure "API key secret not found and no bootstrap script available"
            FAILED_TESTS=$((FAILED_TESTS + 1))
            TEST_RESULTS+=("❌ API Key Verification - Secret not found, no bootstrap")
            if [ "$STOP_ON_FAIL" = true ]; then
                exit 1
            fi
        fi
    fi
}

# Function to generate final report
generate_report() {
    local end_time=$(date)
    local total_duration=$(($(date +%s) - START_TIME))
    
    log_header "TEST EXECUTION SUMMARY"
    
    echo -e "${WHITE}Test Run Details:${NC}"
    echo -e "  Started: $START_DATE"
    echo -e "  Ended: $end_time"
    echo -e "  Duration: ${total_duration}s"
    echo -e "  Mode: $([ "$QUICK_MODE" = true ] && echo "Quick" || echo "Full")"
    echo -e "  Verbose: $([ "$VERBOSE_MODE" = true ] && echo "Yes" || echo "No")"
    
    echo -e "\n${WHITE}Test Results:${NC}"
    echo -e "  ${GREEN}Passed: $PASSED_TESTS${NC}"
    echo -e "  ${RED}Failed: $FAILED_TESTS${NC}"
    echo -e "  ${YELLOW}Skipped: $SKIPPED_TESTS${NC}"
    echo -e "  ${WHITE}Total: $TOTAL_TESTS${NC}"
    
    # Check for frontend failures too
    local frontend_failed=0
    if [ -f "$PROJECT_ROOT/frontend-test-results.json" ]; then
        frontend_failed=$(jq -r '.summary.failed // 0' "$PROJECT_ROOT/frontend-test-results.json")
    fi
    
    local total_failed=$((FAILED_TESTS + frontend_failed))
    
    if [ $total_failed -eq 0 ]; then
        echo -e "\n${GREEN}🎉 ALL TESTS PASSED! 🎉${NC}"
        echo -e "${GREEN}✅ Deployment validation successful${NC}"
    else
        echo -e "\n${RED}💥 SOME TESTS FAILED 💥${NC}"
        echo -e "${RED}❌ Deployment validation failed${NC}"
        
        # Show which tests failed
        echo -e "\n${RED}Failed Tests:${NC}"
        for result in "${TEST_RESULTS[@]}"; do
            if [[ "$result" == *"❌"* ]]; then
                echo -e "  $result"
            fi
        done
        
        # Show frontend failures
        if [ $frontend_failed -gt 0 ] && [ -f "$PROJECT_ROOT/frontend-test-results.json" ]; then
            jq -r '.results[] | select(startswith("❌"))' "$PROJECT_ROOT/frontend-test-results.json" 2>/dev/null | while read -r line; do
                echo -e "  $line"
            done
        fi
    fi
    
    echo -e "\n${WHITE}Detailed Results:${NC}"
    for result in "${TEST_RESULTS[@]}"; do
        echo -e "  $result"
    done
    
    # Generate machine-readable report
    local report_file="$PROJECT_ROOT/test-results.json"
    
    # Check if frontend results exist
    local frontend_section=""
    if [ -f "$PROJECT_ROOT/frontend-test-results.json" ]; then
        frontend_section=$(cat "$PROJECT_ROOT/frontend-test-results.json" | jq '{
            frontend: {
                timestamp: .timestamp,
                duration: .duration,
                summary: .summary,
                success: .success,
                results: .results
            }
        }' | jq -r '.frontend')
    fi
    
    # Generate report with optional frontend section
    if [ -n "$frontend_section" ]; then
        cat > "$report_file" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "duration": $total_duration,
  "mode": "$([ "$QUICK_MODE" = true ] && echo "quick" || echo "full")",
  "backend": {
    "summary": {
      "total": $TOTAL_TESTS,
      "passed": $PASSED_TESTS,
      "failed": $FAILED_TESTS,
      "skipped": $SKIPPED_TESTS
    },
    "success": $([ $FAILED_TESTS -eq 0 ] && echo "true" || echo "false"),
    "results": [
$(printf '      "%s"' "${TEST_RESULTS[0]}")
$(printf ',\n      "%s"' "${TEST_RESULTS[@]:1}")
    ]
  },
  "frontend": $frontend_section,
  "overall": {
    "success": $(if [ $FAILED_TESTS -eq 0 ]; then echo "$frontend_section" | jq -r '.success // true'; else echo "false"; fi)
  }
}
EOF
    else
        cat > "$report_file" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "duration": $total_duration,
  "mode": "$([ "$QUICK_MODE" = true ] && echo "quick" || echo "full")",
  "summary": {
    "total": $TOTAL_TESTS,
    "passed": $PASSED_TESTS,
    "failed": $FAILED_TESTS,
    "skipped": $SKIPPED_TESTS
  },
  "success": $([ $FAILED_TESTS -eq 0 ] && echo "true" || echo "false"),
  "results": [
$(printf '    "%s"' "${TEST_RESULTS[0]}")
$(printf ',\n    "%s"' "${TEST_RESULTS[@]:1}")
  ]
}
EOF
    fi
    
    log_info "Machine-readable report saved to: $report_file"
    
    # Exit with appropriate code (check both backend and frontend)
    local frontend_failed=0
    if [ -f "$PROJECT_ROOT/frontend-test-results.json" ]; then
        frontend_failed=$(jq -r '.summary.failed // 0' "$PROJECT_ROOT/frontend-test-results.json")
    fi
    
    local total_failed=$((FAILED_TESTS + frontend_failed))
    
    if [ $total_failed -eq 0 ]; then
        exit 0
    else
        exit 1
    fi
}

# Trap to ensure report is generated even on interruption
trap 'generate_report' EXIT

# Main execution
START_TIME=$(date +%s)
START_DATE=$(date)

log_header "SIMPLE KANBAN BOARD - COMPREHENSIVE TEST BATTERY"

echo -e "${WHITE}Configuration:${NC}"
echo -e "  Base URL: $BASE_URL"
echo -e "  Namespace: $NAMESPACE"
echo -e "  Secret: $SECRET_NAME"
echo -e "  Quick Mode: $([ "$QUICK_MODE" = true ] && echo "Enabled" || echo "Disabled")"
echo -e "  Verbose Mode: $([ "$VERBOSE_MODE" = true ] && echo "Enabled" || echo "Disabled")"
echo -e "  Stop on Fail: $([ "$STOP_ON_FAIL" = true ] && echo "Enabled" || echo "Disabled")"

# Pre-flight checks
log_header "PRE-FLIGHT CHECKS"
run_health_check
verify_api_key

# Core functionality tests
log_header "CORE FUNCTIONALITY TESTS"

# Export environment variables for child scripts
export BASE_URL
export NAMESPACE
export QUICK_MODE_ENV="$QUICK_MODE"
if [ "$QUICK_MODE" = true ]; then
    run_test_script "test-auth-comprehensive.sh" "Comprehensive Authentication System (Quick)"
else
    run_test_script "test-auth-comprehensive.sh" "Comprehensive Authentication System"
fi

# Test 2: API Key Authentication & Core Endpoints  
run_test_script "test-api-key.sh" "API Key Authentication & Core Endpoints"

# Test 3: Admin Functionality
run_test_script "test-admin.sh" "Admin API & Statistics"

# Test 4: Group Management (if not in quick mode)
if [ "$QUICK_MODE" = false ]; then
    run_test_script "test-groups.sh" "Group Management & Board Sharing"
else
    log_skip "Group Management tests (quick mode)"
    SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
    TEST_RESULTS+=("⏭️  Group Management & Board Sharing - Skipped (quick mode)")
fi

# Test 5: Member Management (if not in quick mode)
if [ "$QUICK_MODE" = false ]; then
    run_test_script "test-member-management.sh" "Member Management & User Search"
else
    log_skip "Member Management tests (quick mode)"
    SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
    TEST_RESULTS+=("⏭️  Member Management & User Search - Skipped (quick mode)")
fi

# Additional smoke tests
log_header "SMOKE TESTS"

# Test static file serving
log_test "Static File Serving"
TOTAL_TESTS=$((TOTAL_TESTS + 1))
static_response=$(curl -s -w "%{http_code}" "$BASE_URL/" -o /dev/null)
if [ "$static_response" = "200" ]; then
    log_success "Main page loads successfully"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    TEST_RESULTS+=("✅ Static File Serving - Main page accessible")
else
    log_failure "Main page failed to load (HTTP $static_response)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    TEST_RESULTS+=("❌ Static File Serving - HTTP $static_response")
fi

# Test API documentation (with authentication)
log_test "API Documentation"
TOTAL_TESTS=$((TOTAL_TESTS + 1))
API_KEY=$(kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" -o jsonpath='{.data.api-key}' | base64 -d 2>/dev/null || echo "")
if [ -n "$API_KEY" ]; then
    docs_response=$(curl -s -w "%{http_code}" -H "Authorization: Bearer $API_KEY" "$BASE_URL/docs" -o /dev/null)
    if [ "$docs_response" = "200" ]; then
        log_success "API documentation accessible with authentication"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        TEST_RESULTS+=("✅ API Documentation - Accessible with auth")
    else
        log_failure "API documentation failed with auth (HTTP $docs_response)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        TEST_RESULTS+=("❌ API Documentation - HTTP $docs_response with auth")
    fi
else
    log_warning "API documentation test skipped (no API key available)"
    SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
    TEST_RESULTS+=("⏭️  API Documentation - Skipped (no API key)")
fi

# Test OpenAPI schema
log_test "OpenAPI Schema"
TOTAL_TESTS=$((TOTAL_TESTS + 1))
openapi_response=$(curl -s -w "%{http_code}" "$BASE_URL/openapi.json" -o /dev/null)
if [ "$openapi_response" = "200" ]; then
    log_success "OpenAPI schema accessible"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    TEST_RESULTS+=("✅ OpenAPI Schema - Accessible")
else
    log_failure "OpenAPI schema failed (HTTP $openapi_response)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    TEST_RESULTS+=("❌ OpenAPI Schema - HTTP $openapi_response")
fi

# Frontend tests (if not in quick mode)
if [ "$QUICK_MODE" = false ]; then
    log_header "FRONTEND TESTS"
    
    log_test "Running Frontend Test Suite"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    # Check if frontend tests are available
    if [ -f "$SCRIPT_DIR/test-frontend-json.sh" ]; then
        if "$SCRIPT_DIR/test-frontend-json.sh" > /tmp/frontend-test-output.log 2>&1; then
            log_success "Frontend tests passed"
            PASSED_TESTS=$((PASSED_TESTS + 1))
            TEST_RESULTS+=("✅ Frontend Test Suite - All tests passed")
            
            # Merge frontend results if JSON exists
            if [ -f "$PROJECT_ROOT/frontend-test-results.json" ]; then
                FRONTEND_PASSED=$(jq -r '.summary.passed // 0' "$PROJECT_ROOT/frontend-test-results.json")
                FRONTEND_FAILED=$(jq -r '.summary.failed // 0' "$PROJECT_ROOT/frontend-test-results.json")
                FRONTEND_TOTAL=$(jq -r '.summary.total // 0' "$PROJECT_ROOT/frontend-test-results.json")
                TEST_RESULTS+=("  📊 Frontend: $FRONTEND_PASSED/$FRONTEND_TOTAL passed")
            fi
        else
            log_failure "Frontend tests failed"
            FAILED_TESTS=$((FAILED_TESTS + 1))
            TEST_RESULTS+=("❌ Frontend Test Suite - Tests failed")
            
            # Still try to get details
            if [ -f "$PROJECT_ROOT/frontend-test-results.json" ]; then
                FRONTEND_PASSED=$(jq -r '.summary.passed // 0' "$PROJECT_ROOT/frontend-test-results.json")
                FRONTEND_FAILED=$(jq -r '.summary.failed // 0' "$PROJECT_ROOT/frontend-test-results.json")
                FRONTEND_TOTAL=$(jq -r '.summary.total // 0' "$PROJECT_ROOT/frontend-test-results.json")
                TEST_RESULTS+=("  📊 Frontend: $FRONTEND_PASSED passed, $FRONTEND_FAILED failed")
            fi
        fi
    else
        log_warning "Frontend test script not found"
        SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
        TEST_RESULTS+=("⏭️  Frontend Test Suite - Script not found")
    fi
else
    log_skip "Frontend tests (quick mode)"
    SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
    TEST_RESULTS+=("⏭️  Frontend Test Suite - Skipped (quick mode)")
fi

log_header "TEST EXECUTION COMPLETE"

# Report will be generated by the trap
