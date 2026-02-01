#!/bin/bash
#
# Run Frontend Tests and Generate JSON Report
#
# This script runs Playwright tests and outputs results in JSON format
# compatible with the test-results.json structure.

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FRONTEND_TEST_DIR="$PROJECT_ROOT/tests/frontend"
OUTPUT_FILE="$PROJECT_ROOT/frontend-test-results.json"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🎭 Running Frontend Tests with JSON Output${NC}"
echo "=============================================="

# Navigate to frontend test directory
cd "$FRONTEND_TEST_DIR"

# Run pytest with JSON output
START_TIME=$(date +%s)
TIMESTAMP=$(date -Iseconds)

# Run tests with parallel execution (2 workers for reliability)
# Use -n 2 for parallel execution to achieve 100% pass rate
if docker-compose run --rm frontend-tests pytest -n 2 --dist loadgroup --json-report --json-report-file=/app/test-results/pytest-report.json -v 2>&1 | tee /tmp/frontend-test-output.txt; then
    TEST_SUCCESS=true
    EXIT_CODE=0
else
    TEST_SUCCESS=false
    EXIT_CODE=$?
fi

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# Check if JSON report was generated
if [ -f "$FRONTEND_TEST_DIR/test-results/pytest-report.json" ]; then
    # Parse pytest JSON report
    TOTAL=$(jq -r '.summary.total // 0' "$FRONTEND_TEST_DIR/test-results/pytest-report.json")
    PASSED=$(jq -r '.summary.passed // 0' "$FRONTEND_TEST_DIR/test-results/pytest-report.json")
    FAILED=$(jq -r '.summary.failed // 0' "$FRONTEND_TEST_DIR/test-results/pytest-report.json")
    SKIPPED=$(jq -r '.summary.skipped // 0' "$FRONTEND_TEST_DIR/test-results/pytest-report.json")
    ERROR=$(jq -r '.summary.error // 0' "$FRONTEND_TEST_DIR/test-results/pytest-report.json")
    
    # Extract test details - simplified to avoid jq issues
    RESULTS=$(jq -r '.tests[] | 
        if .outcome == "passed" then
            "✅ \(.nodeid) - Passed"
        elif .outcome == "failed" then
            "❌ \(.nodeid) - Failed"
        elif .outcome == "skipped" then
            "⏭️  \(.nodeid) - Skipped"
        else
            "⚠️  \(.nodeid) - \(.outcome)"
        end' "$FRONTEND_TEST_DIR/test-results/pytest-report.json" 2>/dev/null | jq -R -s 'split("\n") | map(select(length > 0))' 2>/dev/null || echo '["Error extracting test details"]')
else
    # Fallback: parse from output
    PASSED=$(grep -oP '\d+(?= passed)' /tmp/frontend-test-output.txt | tail -1)
    FAILED=$(grep -oP '\d+(?= failed)' /tmp/frontend-test-output.txt | tail -1)
    SKIPPED=$(grep -oP '\d+(?= skipped)' /tmp/frontend-test-output.txt | tail -1)
    ERROR=$(grep -oP '\d+(?= error)' /tmp/frontend-test-output.txt | tail -1)
    
    # Set defaults if empty
    PASSED=${PASSED:-0}
    FAILED=${FAILED:-0}
    SKIPPED=${SKIPPED:-0}
    ERROR=${ERROR:-0}
    
    # Simple results array
    RESULTS='["Frontend tests completed - see detailed output above"]'
fi

# Calculate totals
TOTAL=$((PASSED + FAILED + SKIPPED + ERROR))

# Generate JSON report
cat > "$OUTPUT_FILE" << EOF
{
  "timestamp": "$TIMESTAMP",
  "duration": $DURATION,
  "test_type": "frontend",
  "summary": {
    "total": $TOTAL,
    "passed": $PASSED,
    "failed": $FAILED,
    "skipped": $SKIPPED,
    "errors": $ERROR
  },
  "success": $([ "$FAILED" -eq 0 ] && [ "$ERROR" -eq 0 ] && echo "true" || echo "false"),
  "results": $RESULTS
}
EOF

echo ""
echo -e "${BLUE}=============================================="
echo "Frontend Test Summary"
echo -e "==============================================  ${NC}"
echo "Total: $TOTAL"
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo "Skipped: $SKIPPED"
echo "Errors: $ERROR"
echo "Duration: ${DURATION}s"
echo ""
echo "JSON report saved to: $OUTPUT_FILE"

if [ "$TEST_SUCCESS" = true ]; then
    echo -e "${GREEN}✅ Frontend tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Frontend tests failed${NC}"
    exit $EXIT_CODE
fi
