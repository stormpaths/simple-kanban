#!/bin/bash
#
# Test Performance Monitoring Script
#
# Monitors API response times and test execution metrics
# during test runs to identify performance bottlenecks.
#

set -e

# Colors
CYAN='\033[0;36m'
WHITE='\033[1;37m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
BASE_URL=${BASE_URL:-https://kanban.stormpath.dev}
INTERVAL=${INTERVAL:-3}  # Seconds between samples
OUTPUT_FILE="test-performance-$(date +%Y%m%d-%H%M%S).log"
CSV_FILE="test-performance-$(date +%Y%m%d-%H%M%S).csv"

echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║${NC} ${WHITE}Test Performance Monitoring${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Target: $BASE_URL"
echo "Sample interval: ${INTERVAL}s"
echo "Output files:"
echo "  • Log: $OUTPUT_FILE"
echo "  • CSV: $CSV_FILE"
echo ""
echo -e "${GREEN}Monitoring API response times...${NC}"
echo ""
echo "Press Ctrl+C to stop monitoring"
echo ""

# CSV Header
echo "Timestamp,Endpoint,Response Time (ms),HTTP Status,Success" > "$CSV_FILE"

# Function to test endpoint
test_endpoint() {
    local endpoint=$1
    local name=$2
    
    local start=$(date +%s%N)
    local status=$(curl -s -o /dev/null -w "%{http_code}" -m 5 "$BASE_URL$endpoint" 2>/dev/null || echo "000")
    local end=$(date +%s%N)
    
    local duration_ns=$((end - start))
    local duration_ms=$((duration_ns / 1000000))
    
    local success="FAIL"
    if [ "$status" = "200" ] || [ "$status" = "401" ] || [ "$status" = "302" ]; then
        success="OK"
    fi
    
    echo "$name,$duration_ms ms,$status,$success"
    echo "$(date +"%Y-%m-%d %H:%M:%S"),$name,$duration_ms,$status,$success" >> "$CSV_FILE"
}

# Monitor loop
{
    echo "=== Test Performance Monitoring Started ==="
    echo "Timestamp: $(date)"
    echo "Target: $BASE_URL"
    echo ""
} | tee "$OUTPUT_FILE"

ITERATION=1

while true; do
    TIMESTAMP=$(date +"%H:%M:%S")
    
    {
        echo "[$TIMESTAMP] Iteration $ITERATION"
        echo "----------------------------------------"
        
        # Test various endpoints
        test_endpoint "/" "Homepage"
        test_endpoint "/api/health" "Health Check"
        test_endpoint "/api/boards/" "Boards API"
        test_endpoint "/api/groups/" "Groups API"
        test_endpoint "/docs" "API Docs"
        
        echo ""
    } | tee -a "$OUTPUT_FILE"
    
    ITERATION=$((ITERATION + 1))
    sleep "$INTERVAL"
done
