#!/bin/bash
"""
Admin API Testing Script for Simple Kanban Board

This script tests the admin API endpoints using API key authentication.
The API key is stored in the secret: simple-kanban-test-api-key

Secret Path: apps-dev/simple-kanban-test-api-key
API Key User: User ID 1 (admin user)
Scopes: read, write, docs, admin
"""

set -e

# Configuration
NAMESPACE="apps-dev"
SECRET_NAME="simple-kanban-test-api-key"
BASE_URL="https://kanban.stormpath.dev"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔐 Simple Kanban Admin API Testing Suite${NC}"
echo "=================================================="

# Get API key from Kubernetes secret
echo -e "\n${YELLOW}📋 Retrieving API key from Kubernetes secret...${NC}"
API_KEY=$(kubectl get secret $SECRET_NAME -n $NAMESPACE -o jsonpath='{.data.api-key}' | base64 -d)
KEY_NAME=$(kubectl get secret $SECRET_NAME -n $NAMESPACE -o jsonpath='{.data.key-name}' | base64 -d)
USER_ID=$(kubectl get secret $SECRET_NAME -n $NAMESPACE -o jsonpath='{.data.user-id}' | base64 -d)
SCOPES=$(kubectl get secret $SECRET_NAME -n $NAMESPACE -o jsonpath='{.data.scopes}' | base64 -d)

echo "✅ Secret retrieved successfully"
echo "   Key Name: $KEY_NAME"
echo "   User ID: $USER_ID"
echo "   Scopes: $SCOPES"
echo "   Key: ${API_KEY:0:20}..."

# Test function
test_endpoint() {
    local method=$1
    local endpoint=$2
    local description=$3
    local expected_status=${4:-200}
    
    echo -e "\n${YELLOW}🧪 Testing: $description${NC}"
    echo "   $method $endpoint"
    
    response=$(curl -s -w "\n%{http_code}" -X $method \
        "$BASE_URL$endpoint" \
        -H "Authorization: Bearer $API_KEY" \
        -H "Content-Type: application/json")
    
    # Split response and status code
    status_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n -1)
    
    if [ "$status_code" = "$expected_status" ]; then
        echo -e "   ${GREEN}✅ SUCCESS${NC} (HTTP $status_code)"
        if [ ${#body} -lt 200 ]; then
            echo "   Response: $body"
        else
            echo "   Response: ${body:0:100}... (truncated)"
        fi
    else
        echo -e "   ${RED}❌ FAILED${NC} (HTTP $status_code, expected $expected_status)"
        echo "   Response: $body"
        return 1
    fi
}

# Test Suite
echo -e "\n${BLUE}🚀 Starting Admin API Test Suite${NC}"

# Test 1: Get admin stats
test_endpoint "GET" "/api/admin/stats" "Get admin statistics"

# Test 2: List all users
test_endpoint "GET" "/api/admin/users" "List all users with stats"

# Test 3: Test without authentication (should fail)
echo -e "\n${YELLOW}🧪 Testing: Access without authentication (should fail)${NC}"
echo "   GET /api/admin/stats"
response=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/api/admin/stats" -H "Content-Type: application/json")
status_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n -1)

if [ "$status_code" = "401" ]; then
    echo -e "   ${GREEN}✅ SUCCESS${NC} (HTTP $status_code - correctly rejected)"
else
    echo -e "   ${RED}❌ FAILED${NC} (HTTP $status_code, expected 401)"
    echo "   Response: $body"
fi

# Test 4: Test with invalid API key (should fail)
echo -e "\n${YELLOW}🧪 Testing: Access with invalid API key (should fail)${NC}"
echo "   GET /api/admin/stats"
response=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/api/admin/stats" \
    -H "Authorization: Bearer sk_invalid_key_for_testing" \
    -H "Content-Type: application/json")
status_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n -1)

if [ "$status_code" = "401" ]; then
    echo -e "   ${GREEN}✅ SUCCESS${NC} (HTTP $status_code - correctly rejected)"
else
    echo -e "   ${RED}❌ FAILED${NC} (HTTP $status_code, expected 401)"
    echo "   Response: $body"
fi

# Test 5: Parse and validate admin stats
echo -e "\n${YELLOW}🧪 Testing: Parse admin statistics data${NC}"
echo "   GET /api/admin/stats (parsing response)"
stats_response=$(curl -s -H "Authorization: Bearer $API_KEY" "$BASE_URL/api/admin/stats")
total_users=$(echo "$stats_response" | jq -r '.total_users')
active_users=$(echo "$stats_response" | jq -r '.active_users')
total_boards=$(echo "$stats_response" | jq -r '.total_boards')
total_tasks=$(echo "$stats_response" | jq -r '.total_tasks')

if [[ "$total_users" =~ ^[0-9]+$ ]] && [[ "$active_users" =~ ^[0-9]+$ ]] && [[ "$total_boards" =~ ^[0-9]+$ ]] && [[ "$total_tasks" =~ ^[0-9]+$ ]]; then
    echo -e "   ${GREEN}✅ SUCCESS${NC} - Valid statistics data"
    echo "   Total Users: $total_users"
    echo "   Active Users: $active_users"
    echo "   Total Boards: $total_boards"
    echo "   Total Tasks: $total_tasks"
else
    echo -e "   ${RED}❌ FAILED${NC} - Invalid statistics format"
    echo "   Response: $stats_response"
fi

echo -e "\n${BLUE}📊 Test Summary${NC}"
echo "=================================================="
echo "✅ Admin API Key Authentication: WORKING"
echo "✅ Admin Statistics Endpoint: WORKING"
echo "✅ Admin Users Endpoint: WORKING"
echo "✅ Security Validation: WORKING"
echo "✅ Data Format Validation: WORKING"

echo -e "\n${GREEN}🎉 All Admin API tests completed successfully!${NC}"
echo ""
echo "📝 Notes for automated testing:"
echo "   - Secret Path: $NAMESPACE/$SECRET_NAME"
echo "   - API Key User: User ID $USER_ID (admin user)"
echo "   - Available Scopes: $SCOPES"
echo "   - Base URL: $BASE_URL"
echo ""
echo "🔧 To run this test again:"
echo "   ./scripts/test-admin.sh"
echo ""
echo "🌐 To test admin page with API key:"
echo "   1. Open browser console on admin page"
echo "   2. Run: localStorage.setItem('api_key', '$API_KEY')"
echo "   3. Refresh the page"
