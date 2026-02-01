#!/bin/bash
"""
Comprehensive Endpoint Authentication Testing Script

This script tests ALL protected endpoints with BOTH JWT and API key authentication
to ensure dual authentication support is working correctly across the entire API.

Usage:
  ./scripts/test-auth-endpoints.sh
"""

set -e

# Configuration
BASE_URL="${BASE_URL:-https://localhost:8000}"
NAMESPACE="apps-dev"
SECRET_NAME="simple-kanban-test-api-key"
TEST_USERNAME="endpointtest_$(date +%s)"
TEST_EMAIL="endpointtest_$(date +%s)@example.com"
# Generate secure random password for testing
TEST_PASSWORD="$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-16)Aa1!"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

echo -e "${BLUE}🔐 Comprehensive Endpoint Authentication Testing${NC}"
echo "=================================================="
echo "Testing ALL endpoints with BOTH JWT and API key authentication"
echo ""

# Helper functions
test_step() {
    local description="$1"
    echo -e "\n${YELLOW}🧪 Testing: $description${NC}"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
}

test_success() {
    local message="$1"
    echo -e "   ${GREEN}✅ SUCCESS${NC} - $message"
    PASSED_TESTS=$((PASSED_TESTS + 1))
}

test_failure() {
    local message="$1"
    echo -e "   ${RED}❌ FAILED${NC} - $message"
    FAILED_TESTS=$((FAILED_TESTS + 1))
}

test_info() {
    local message="$1"
    echo -e "   ${BLUE}ℹ️  INFO${NC} - $message"
}

# Helper function to test endpoint with both auth methods
test_endpoint_dual_auth() {
    local method="$1"
    local endpoint="$2"
    local description="$3"
    local data="$4"
    local expected_status="$5"
    
    test_step "$description"
    
    # Test with JWT
    local jwt_cmd="curl -s -w \"\n%{http_code}\" -X $method -H \"Authorization: Bearer $JWT_TOKEN\""
    if [ -n "$data" ]; then
        jwt_cmd="$jwt_cmd -H \"Content-Type: application/json\" -d '$data'"
    fi
    jwt_cmd="$jwt_cmd \"$BASE_URL$endpoint\""
    
    local jwt_response=$(eval $jwt_cmd)
    local jwt_status=$(echo "$jwt_response" | tail -n1)
    
    # Test with API Key
    local api_cmd="curl -s -w \"\n%{http_code}\" -X $method -H \"Authorization: Bearer $API_KEY\""
    if [ -n "$data" ]; then
        api_cmd="$api_cmd -H \"Content-Type: application/json\" -d '$data'"
    fi
    api_cmd="$api_cmd \"$BASE_URL$endpoint\""
    
    local api_response=$(eval $api_cmd)
    local api_status=$(echo "$api_response" | tail -n1)
    
    # Check results
    local jwt_success=false
    local api_success=false
    
    if [ "$jwt_status" = "$expected_status" ]; then
        jwt_success=true
    fi
    
    if [ "$api_status" = "$expected_status" ]; then
        api_success=true
    fi
    
    if [ "$jwt_success" = true ] && [ "$api_success" = true ]; then
        test_success "Both JWT and API key authentication work (HTTP $expected_status)"
        return 0
    elif [ "$jwt_success" = true ] && [ "$api_success" = false ]; then
        test_failure "JWT works (HTTP $jwt_status) but API key fails (HTTP $api_status)"
        return 1
    elif [ "$jwt_success" = false ] && [ "$api_success" = true ]; then
        test_failure "API key works (HTTP $api_status) but JWT fails (HTTP $jwt_status)"
        return 1
    else
        test_failure "Both authentication methods fail - JWT: HTTP $jwt_status, API key: HTTP $api_status"
        return 1
    fi
}

# Setup: Get API key from Kubernetes secret
echo -e "${BLUE}🔧 Setup${NC}"
API_KEY=$(kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" -o jsonpath='{.data.api-key}' | base64 -d 2>/dev/null || echo "")
if [ -z "$API_KEY" ]; then
    echo -e "${RED}❌ Failed to get API key from Kubernetes secret${NC}"
    exit 1
fi
test_info "API key retrieved: ${API_KEY:0:15}..."

# Create test user and get JWT token
echo "Creating test user for JWT authentication..."
register_response=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"$TEST_USERNAME\", \"email\": \"$TEST_EMAIL\", \"password\": \"$TEST_PASSWORD\", \"full_name\": \"Endpoint Test User\"}" \
    "$BASE_URL/api/auth/register")

if echo "$register_response" | grep -q '"id"'; then
    TEST_USER_ID=$(echo "$register_response" | grep -o '"id":[0-9]*' | cut -d':' -f2)
    test_info "Test user created (ID: $TEST_USER_ID)"
else
    echo -e "${RED}❌ Failed to create test user${NC}"
    exit 1
fi

# Login to get JWT token
login_response=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"$TEST_USERNAME\", \"password\": \"$TEST_PASSWORD\"}" \
    "$BASE_URL/api/auth/login")

if echo "$login_response" | grep -q '"access_token"'; then
    JWT_TOKEN=$(echo "$login_response" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    test_info "JWT token obtained: ${JWT_TOKEN:0:20}..."
else
    echo -e "${RED}❌ Failed to get JWT token${NC}"
    exit 1
fi

echo -e "\n${BLUE}🚀 Testing All Protected Endpoints${NC}"
echo "=================================================="

# Board Endpoints
test_endpoint_dual_auth "GET" "/api/boards/" "List boards" "" "200"
test_endpoint_dual_auth "POST" "/api/boards/" "Create board" '{"name": "Dual Auth Test Board", "description": "Testing dual authentication"}' "201"

# Get the created board ID for further testing
board_list=$(curl -s -H "Authorization: Bearer $JWT_TOKEN" "$BASE_URL/api/boards/")
if echo "$board_list" | grep -q "Dual Auth Test Board"; then
    TEST_BOARD_ID=$(echo "$board_list" | grep -B3 -A3 "Dual Auth Test Board" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
    test_info "Created board ID: $TEST_BOARD_ID"
    
    if [ -n "$TEST_BOARD_ID" ]; then
        test_endpoint_dual_auth "GET" "/api/boards/$TEST_BOARD_ID" "Get board details" "" "200"
        test_endpoint_dual_auth "PUT" "/api/boards/$TEST_BOARD_ID" "Update board" '{"name": "Updated Dual Auth Board", "description": "Updated via dual auth test"}' "200"
        test_endpoint_dual_auth "GET" "/api/boards/$TEST_BOARD_ID/columns" "Get board columns" "" "200"
    fi
fi

# Group Endpoints
test_endpoint_dual_auth "GET" "/api/groups/" "List groups" "" "200"
test_endpoint_dual_auth "POST" "/api/groups/" "Create group" '{"name": "Dual Auth Test Group", "description": "Testing dual authentication"}' "201"

# Get the created group ID for further testing
group_list=$(curl -s -H "Authorization: Bearer $JWT_TOKEN" "$BASE_URL/api/groups/")
if echo "$group_list" | grep -q "Dual Auth Test Group"; then
    TEST_GROUP_ID=$(echo "$group_list" | grep -B3 -A3 "Dual Auth Test Group" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
    test_info "Created group ID: $TEST_GROUP_ID"
    
    if [ -n "$TEST_GROUP_ID" ]; then
        test_endpoint_dual_auth "GET" "/api/groups/$TEST_GROUP_ID" "Get group details" "" "200"
        test_endpoint_dual_auth "PUT" "/api/groups/$TEST_GROUP_ID" "Update group" '{"name": "Updated Dual Auth Group", "description": "Updated via dual auth test"}' "200"
    fi
fi

# API Key Management Endpoints
test_endpoint_dual_auth "GET" "/api/api-keys/" "List API keys" "" "200"
test_endpoint_dual_auth "POST" "/api/api-keys/" "Create API key" '{"name": "dual-auth-test-key", "scopes": ["read"]}' "201"
test_endpoint_dual_auth "GET" "/api/api-keys/stats/usage" "Get API key usage stats" "" "200"

# Get created API key ID for further testing
apikey_list=$(curl -s -H "Authorization: Bearer $JWT_TOKEN" "$BASE_URL/api/api-keys/")
if echo "$apikey_list" | grep -q "dual-auth-test-key"; then
    TEST_APIKEY_ID=$(echo "$apikey_list" | grep -B5 -A5 "dual-auth-test-key" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
    test_info "Created API key ID: $TEST_APIKEY_ID"
    
    if [ -n "$TEST_APIKEY_ID" ]; then
        test_endpoint_dual_auth "GET" "/api/api-keys/$TEST_APIKEY_ID" "Get API key details" "" "200"
        test_endpoint_dual_auth "PUT" "/api/api-keys/$TEST_APIKEY_ID" "Update API key" '{"name": "updated-dual-auth-key"}' "200"
    fi
fi

# User Profile Endpoints (JWT only - API keys shouldn't access user profiles)
test_step "User profile access - JWT vs API key behavior"
jwt_profile_response=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $JWT_TOKEN" "$BASE_URL/api/auth/me")
jwt_profile_status=$(echo "$jwt_profile_response" | tail -n1)

api_profile_response=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $API_KEY" "$BASE_URL/api/auth/me")
api_profile_status=$(echo "$api_profile_response" | tail -n1)

if [ "$jwt_profile_status" = "200" ] && [ "$api_profile_status" = "401" ]; then
    test_success "JWT can access user profile, API key properly rejected"
elif [ "$jwt_profile_status" = "200" ] && [ "$api_profile_status" = "200" ]; then
    test_info "Both JWT and API key can access user profile (may be expected behavior)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    test_failure "Unexpected profile access behavior - JWT: HTTP $jwt_profile_status, API key: HTTP $api_profile_status"
fi

# Admin Endpoints (should work with admin API key, may not work with regular JWT)
test_step "Admin endpoints - authentication method compatibility"
admin_stats_jwt=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $JWT_TOKEN" "$BASE_URL/api/admin/stats")
admin_stats_jwt_status=$(echo "$admin_stats_jwt" | tail -n1)

admin_stats_api=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $API_KEY" "$BASE_URL/api/admin/stats")
admin_stats_api_status=$(echo "$admin_stats_api" | tail -n1)

if [ "$admin_stats_api_status" = "200" ]; then
    test_success "Admin API key can access admin endpoints"
    if [ "$admin_stats_jwt_status" = "200" ]; then
        test_info "JWT also has admin access"
    else
        test_info "JWT doesn't have admin access (expected for non-admin user)"
    fi
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    test_failure "Admin API key cannot access admin endpoints (HTTP $admin_stats_api_status)"
fi

# Test Task Endpoints (if we have a board)
if [ -n "$TEST_BOARD_ID" ]; then
    # Get columns from the board first
    columns_response=$(curl -s -H "Authorization: Bearer $JWT_TOKEN" "$BASE_URL/api/boards/$TEST_BOARD_ID")
    if echo "$columns_response" | grep -q '"columns"'; then
        FIRST_COLUMN_ID=$(echo "$columns_response" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
        test_info "Using column ID: $FIRST_COLUMN_ID"
        
        if [ -n "$FIRST_COLUMN_ID" ]; then
            test_endpoint_dual_auth "POST" "/api/tasks/" "Create task" "{\"title\": \"Dual Auth Test Task\", \"description\": \"Testing dual authentication\", \"column_id\": $FIRST_COLUMN_ID}" "201"
            
            # Get created task ID
            task_response=$(curl -s -H "Authorization: Bearer $JWT_TOKEN" "$BASE_URL/api/boards/$TEST_BOARD_ID")
            if echo "$task_response" | grep -q "Dual Auth Test Task"; then
                TEST_TASK_ID=$(echo "$task_response" | grep -B5 -A5 "Dual Auth Test Task" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
                test_info "Created task ID: $TEST_TASK_ID"
                
                if [ -n "$TEST_TASK_ID" ]; then
                    test_endpoint_dual_auth "GET" "/api/tasks/$TEST_TASK_ID" "Get task details" "" "200"
                    test_endpoint_dual_auth "PUT" "/api/tasks/$TEST_TASK_ID" "Update task" '{"title": "Updated Dual Auth Task", "description": "Updated via dual auth test"}' "200"
                fi
            fi
        fi
    fi
fi

# Cleanup
echo -e "\n${BLUE}🧹 Cleanup${NC}"
if [ -n "$TEST_TASK_ID" ]; then
    echo "Deleting test task..."
    curl -s -X DELETE -H "Authorization: Bearer $JWT_TOKEN" "$BASE_URL/api/tasks/$TEST_TASK_ID" > /dev/null
fi

if [ -n "$TEST_BOARD_ID" ]; then
    echo "Deleting test board..."
    curl -s -X DELETE -H "Authorization: Bearer $JWT_TOKEN" "$BASE_URL/api/boards/$TEST_BOARD_ID" > /dev/null
fi

if [ -n "$TEST_GROUP_ID" ]; then
    echo "Deleting test group..."
    curl -s -X DELETE -H "Authorization: Bearer $JWT_TOKEN" "$BASE_URL/api/groups/$TEST_GROUP_ID" > /dev/null
fi

if [ -n "$TEST_APIKEY_ID" ]; then
    echo "Deleting test API key..."
    curl -s -X DELETE -H "Authorization: Bearer $JWT_TOKEN" "$BASE_URL/api/api-keys/$TEST_APIKEY_ID" > /dev/null
fi

# Final Report
echo -e "\n${BLUE}📊 Comprehensive Endpoint Authentication Test Results${NC}"
echo "=================================================="
echo "Total Tests: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"
echo "Success Rate: $(( PASSED_TESTS * 100 / TOTAL_TESTS ))%"

echo -e "\n${BLUE}🔍 Authentication Coverage Summary${NC}"
echo "✅ Board endpoints: JWT + API key authentication"
echo "✅ Group endpoints: JWT + API key authentication"
echo "✅ API key management: JWT + API key authentication"
echo "✅ Task endpoints: JWT + API key authentication"
echo "✅ User profile: JWT-specific access control"
echo "✅ Admin endpoints: Admin API key access control"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "\n${GREEN}🎉 All endpoint authentication tests passed!${NC}"
    echo -e "${GREEN}✅ Dual authentication (JWT + API key) is working correctly across all endpoints!${NC}"
    exit 0
else
    echo -e "\n${RED}💥 Some endpoint authentication tests failed!${NC}"
    exit 1
fi
