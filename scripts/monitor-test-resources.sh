#!/bin/bash
#
# Test Resource Monitoring Script
#
# Monitors backend pod resources during test execution
# to identify bottlenecks and optimize resource allocation.
#

set -e

# Colors
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

# Configuration
NAMESPACE=${NAMESPACE:-simple-kanban}
INTERVAL=${INTERVAL:-5}  # Seconds between samples
OUTPUT_FILE="test-resources-$(date +%Y%m%d-%H%M%S).log"

echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║${NC} ${WHITE}Test Resource Monitoring${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Namespace: $NAMESPACE"
echo "Sample interval: ${INTERVAL}s"
echo "Output file: $OUTPUT_FILE"
echo ""
echo "Press Ctrl+C to stop monitoring"
echo ""

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "Error: kubectl not found. Please install kubectl."
    exit 1
fi

# Check if namespace exists
if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
    echo "Warning: Namespace '$NAMESPACE' not found or not accessible"
    echo "Attempting to monitor anyway..."
fi

# Header
echo "Timestamp,Pod,CPU(cores),Memory(bytes)" | tee "$OUTPUT_FILE"

# Monitor loop
while true; do
    TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
    
    # Get pod metrics
    kubectl top pods -n "$NAMESPACE" --no-headers 2>/dev/null | while read -r line; do
        POD=$(echo "$line" | awk '{print $1}')
        CPU=$(echo "$line" | awk '{print $2}')
        MEMORY=$(echo "$line" | awk '{print $3}')
        
        # Only monitor kanban pods
        if [[ "$POD" == *"kanban"* ]]; then
            echo "$TIMESTAMP,$POD,$CPU,$MEMORY" | tee -a "$OUTPUT_FILE"
        fi
    done
    
    sleep "$INTERVAL"
done
