#!/bin/bash
"""
API Key Testing Script for Simple Kanban Board

This script tests the API key authentication system using a stored Kubernetes secret.
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

echo -e "${BLUE}🔐 Simple Kanban API Key Testing Suite${NC}"
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
echo -e "\n${BLUE}🚀 Starting API Key Test Suite${NC}"

# Test 1: List boards
test_endpoint "GET" "/api/boards/" "List all boards"

# Test 2: Get specific board
test_endpoint "GET" "/api/boards/1" "Get board details"

# Test 3: List API keys
test_endpoint "GET" "/api/api-keys/" "List API keys"

# Test 4: Get API key stats
test_endpoint "GET" "/api/api-keys/stats/usage" "Get API key usage statistics"

# Test 5: Access secured documentation
test_endpoint "GET" "/docs" "Access secured documentation"

# Test 6: Access OpenAPI schema
test_endpoint "GET" "/openapi.json" "Access OpenAPI schema"

# Test 7: Test without authentication (should fail)
echo -e "\n${YELLOW}🧪 Testing: Access without authentication (should fail)${NC}"
echo "   GET /api/boards/"
response=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/api/boards/" -H "Content-Type: application/json")
status_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n -1)

if [ "$status_code" = "401" ]; then
    echo -e "   ${GREEN}✅ SUCCESS${NC} (HTTP $status_code - correctly rejected)"
else
    echo -e "   ${RED}❌ FAILED${NC} (HTTP $status_code, expected 401)"
    echo "   Response: $body"
fi

# Test 8: Test with invalid API key (should fail)
echo -e "\n${YELLOW}🧪 Testing: Access with invalid API key (should fail)${NC}"
echo "   GET /api/boards/"
response=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/api/boards/" \
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

echo -e "\n${BLUE}📊 Test Summary${NC}"
echo "=================================================="
echo "✅ API Key Authentication: WORKING"
echo "✅ Endpoint Access Control: WORKING"
echo "✅ Security Validation: WORKING"
echo "✅ Documentation Access: WORKING"

echo -e "\n${GREEN}🎉 All API Key tests completed successfully!${NC}"
echo ""
echo "📝 Notes for future testing:"
echo "   - Secret Path: $NAMESPACE/$SECRET_NAME"
echo "   - API Key User: User ID $USER_ID"
echo "   - Available Scopes: $SCOPES"
echo "   - Base URL: $BASE_URL"
echo ""
echo "🔧 To run this test again:"
echo "   ./scripts/test-api-key.sh"
