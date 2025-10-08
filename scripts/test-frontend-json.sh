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

# Run tests and capture output
if docker-compose run --rm frontend-tests pytest --json-report --json-report-file=/app/test-results/pytest-report.json -v 2>&1 | tee /tmp/frontend-test-output.txt; then
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
    
    # Extract test details
    RESULTS=$(jq -r '.tests[] | 
        if .outcome == "passed" then
            "✅ \(.nodeid | split("::")[1:] | join(" - ")) - Passed (\(.duration | tonumber | round)s)"
        elif .outcome == "failed" then
            "❌ \(.nodeid | split("::")[1:] | join(" - ")) - Failed: \(.call.longrepr.reprcrash.message // "Unknown error")"
        elif .outcome == "skipped" then
            "⏭️  \(.nodeid | split("::")[1:] | join(" - ")) - Skipped"
        else
            "⚠️  \(.nodeid | split("::")[1:] | join(" - ")) - \(.outcome)"
        end' "$FRONTEND_TEST_DIR/test-results/pytest-report.json" | jq -R -s 'split("\n") | map(select(length > 0))')
else
    # Fallback: parse from output
    TOTAL=$(grep -oP '\d+(?= passed)' /tmp/frontend-test-output.txt | tail -1 || echo "0")
    PASSED=$TOTAL
    FAILED=$(grep -oP '\d+(?= failed)' /tmp/frontend-test-output.txt | tail -1 || echo "0")
    SKIPPED=$(grep -oP '\d+(?= skipped)' /tmp/frontend-test-output.txt | tail -1 || echo "0")
    ERROR=$(grep -oP '\d+(?= error)' /tmp/frontend-test-output.txt | tail -1 || echo "0")
    
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
