#!/bin/bash
#
# Docker Container Resource Monitoring Script
#
# Monitors Docker container resources during test execution
# to identify bottlenecks and optimize resource allocation.
#

set -e

# Colors
CYAN='\033[0;36m'
WHITE='\033[1;37m'
GREEN='\033[0;32m'
NC='\033[0m'

# Configuration
INTERVAL=${INTERVAL:-2}  # Seconds between samples
OUTPUT_FILE="docker-resources-$(date +%Y%m%d-%H%M%S).log"

echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║${NC} ${WHITE}Docker Resource Monitoring${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Sample interval: ${INTERVAL}s"
echo "Output file: $OUTPUT_FILE"
echo ""
echo -e "${GREEN}Monitoring containers matching: kanban, postgres, redis${NC}"
echo ""
echo "Press Ctrl+C to stop monitoring"
echo ""

# Check if docker is available
if ! command -v docker &> /dev/null; then
    echo "Error: docker not found. Please install docker."
    exit 1
fi

# Header
{
    echo "Timestamp,Container,CPU%,Memory Usage,Memory Limit,Memory%,Net I/O,Block I/O"
} | tee "$OUTPUT_FILE"

# Monitor loop
while true; do
    TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
    
    # Get container stats (one-shot, no streaming)
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}" 2>/dev/null | \
    tail -n +2 | while IFS=$'\t' read -r CONTAINER CPU MEM_USAGE MEM_PERC NET_IO BLOCK_IO; do
        # Only monitor relevant containers
        if [[ "$CONTAINER" == *"kanban"* ]] || \
           [[ "$CONTAINER" == *"postgres"* ]] || \
           [[ "$CONTAINER" == *"redis"* ]] || \
           [[ "$CONTAINER" == *"frontend-tests"* ]]; then
            
            # Parse memory usage (e.g., "123MiB / 2GiB")
            MEM_USED=$(echo "$MEM_USAGE" | awk '{print $1}')
            MEM_LIMIT=$(echo "$MEM_USAGE" | awk '{print $3}')
            
            echo "$TIMESTAMP,$CONTAINER,$CPU,$MEM_USED,$MEM_LIMIT,$MEM_PERC,$NET_IO,$BLOCK_IO" | tee -a "$OUTPUT_FILE"
        fi
    done
    
    sleep "$INTERVAL"
done
