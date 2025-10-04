#!/bin/bash
"""
JWT Authentication Testing Script for Simple Kanban Board

This script tests the JWT authentication system including:
- User login flow
- JWT token validation
- Protected endpoint access
- Token expiration handling
- Cross-authentication with API keys

Usage:
  ./scripts/test-auth-jwt.sh
"""

set -e

# Configuration
BASE_URL="https://kanban.stormpath.dev"
TEST_USERNAME="jwttest_$(date +%s)"
TEST_EMAIL="jwttest_$(date +%s)@example.com"
TEST_PASSWORD="SecureTestPassword123!"
TEST_FULL_NAME="JWT Test User"

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

echo -e "${BLUE}🔐 JWT Authentication Testing Suite${NC}"
echo "=================================================="
echo "Test User: $TEST_USERNAME"
echo "Test Email: $TEST_EMAIL"
echo ""

# Helper function for test output
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

# Helper function to make API calls and check status
api_call() {
    local method="$1"
    local endpoint="$2"
    local data="$3"
    local auth_header="$4"
    local expected_status="$5"
    
    local curl_cmd="curl -s -w \"\n%{http_code}\" -X $method"
    
    if [ -n "$auth_header" ]; then
        curl_cmd="$curl_cmd -H \"Authorization: Bearer $auth_header\""
    fi
    
    if [ -n "$data" ]; then
        curl_cmd="$curl_cmd -H \"Content-Type: application/json\" -d '$data'"
    fi
    
    curl_cmd="$curl_cmd \"$BASE_URL$endpoint\""
    
    local response=$(eval $curl_cmd)
    local status_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | head -n -1)
    
    if [ "$status_code" = "$expected_status" ]; then
        return 0
    else
        echo "Expected: $expected_status, Got: $status_code"
        echo "Response: $body"
        return 1
    fi
}

# Test 1: Create test user for JWT testing
test_step "Create test user for JWT authentication"
register_response=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"$TEST_USERNAME\", \"email\": \"$TEST_EMAIL\", \"password\": \"$TEST_PASSWORD\", \"full_name\": \"$TEST_FULL_NAME\"}" \
    "$BASE_URL/api/auth/register")

if echo "$register_response" | grep -q '"id"'; then
    TEST_USER_ID=$(echo "$register_response" | grep -o '"id":[0-9]*' | cut -d':' -f2)
    test_success "Test user created successfully (ID: $TEST_USER_ID)"
else
    test_failure "Failed to create test user: $register_response"
    exit 1
fi

# Test 2: JWT Login Flow
test_step "JWT login with valid credentials"
login_response=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"$TEST_USERNAME\", \"password\": \"$TEST_PASSWORD\"}" \
    "$BASE_URL/api/auth/login")

if echo "$login_response" | grep -q '"access_token"'; then
    JWT_TOKEN=$(echo "$login_response" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    TOKEN_TYPE=$(echo "$login_response" | grep -o '"token_type":"[^"]*' | cut -d'"' -f4)
    EXPIRES_IN=$(echo "$login_response" | grep -o '"expires_in":[0-9]*' | cut -d':' -f2)
    
    test_success "JWT login successful"
    test_info "Token type: $TOKEN_TYPE"
    test_info "Expires in: $EXPIRES_IN seconds"
    test_info "Token: ${JWT_TOKEN:0:20}..."
else
    test_failure "JWT login failed: $login_response"
    exit 1
fi

# Test 3: JWT Token Validation - Access Protected Endpoint
test_step "JWT token validation - access boards endpoint"
if api_call "GET" "/api/boards/" "" "$JWT_TOKEN" "200"; then
    test_success "JWT token successfully accessed protected endpoint"
else
    test_failure "JWT token failed to access protected endpoint"
fi

# Test 4: JWT Token - Create Board
test_step "JWT token - create new board"
board_data='{"name": "JWT Test Board", "description": "Board created via JWT authentication"}'
create_response=$(curl -s -X POST \
    -H "Authorization: Bearer $JWT_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$board_data" \
    "$BASE_URL/api/boards/")

if echo "$create_response" | grep -q '"id"'; then
    TEST_BOARD_ID=$(echo "$create_response" | grep -o '"id":[0-9]*' | cut -d':' -f2)
    test_success "Board created successfully via JWT (ID: $TEST_BOARD_ID)"
else
    test_failure "Failed to create board via JWT: $create_response"
fi

# Test 5: JWT Token - Create Group
test_step "JWT token - create new group"
group_data='{"name": "JWT Test Group", "description": "Group created via JWT authentication"}'
group_response=$(curl -s -X POST \
    -H "Authorization: Bearer $JWT_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$group_data" \
    "$BASE_URL/api/groups/")

if echo "$group_response" | grep -q '"id"'; then
    TEST_GROUP_ID=$(echo "$group_response" | grep -o '"id":[0-9]*' | cut -d':' -f2)
    test_success "Group created successfully via JWT (ID: $TEST_GROUP_ID)"
else
    test_failure "Failed to create group via JWT: $group_response"
fi

# Test 6: JWT Token - Create API Key
test_step "JWT token - create API key"
apikey_data='{"name": "jwt-created-key", "scopes": ["read", "write"]}'
apikey_response=$(curl -s -X POST \
    -H "Authorization: Bearer $JWT_TOKEN" \
    -H "Content-Type: application/json" \
    -d "$apikey_data" \
    "$BASE_URL/api/api-keys/")

if echo "$apikey_response" | grep -q '"api_key"'; then
    CREATED_API_KEY=$(echo "$apikey_response" | grep -o '"api_key":"[^"]*' | cut -d'"' -f4)
    test_success "API key created successfully via JWT"
    test_info "Created API key: ${CREATED_API_KEY:0:15}..."
else
    test_failure "Failed to create API key via JWT: $apikey_response"
fi

# Test 7: Cross-Authentication - Use JWT-created API key
if [ -n "$CREATED_API_KEY" ]; then
    test_step "Cross-authentication - use JWT-created API key"
    if api_call "GET" "/api/boards/" "" "$CREATED_API_KEY" "200"; then
        test_success "JWT-created API key successfully accessed protected endpoint"
    else
        test_failure "JWT-created API key failed to access protected endpoint"
    fi
fi

# Test 8: JWT Token - Access User Profile
test_step "JWT token - access user profile"
profile_response=$(curl -s -H "Authorization: Bearer $JWT_TOKEN" "$BASE_URL/api/auth/me")

if echo "$profile_response" | grep -q "\"username\":\"$TEST_USERNAME\""; then
    test_success "User profile accessed successfully via JWT"
else
    test_failure "Failed to access user profile via JWT: $profile_response"
fi

# Test 9: Invalid JWT Token Rejection
test_step "Invalid JWT token rejection"
invalid_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature"
if api_call "GET" "/api/boards/" "" "$invalid_token" "401"; then
    test_success "Invalid JWT token properly rejected"
else
    test_failure "Invalid JWT token was not rejected"
fi

# Test 10: No Authentication Rejection
test_step "No authentication rejection"
if api_call "GET" "/api/boards/" "" "" "401"; then
    test_success "Unauthenticated request properly rejected"
else
    test_failure "Unauthenticated request was not rejected"
fi

# Test 11: JWT Login with Invalid Credentials
test_step "JWT login with invalid password"
invalid_login_response=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"$TEST_USERNAME\", \"password\": \"wrongpassword\"}" \
    "$BASE_URL/api/auth/login")

invalid_status=$(echo "$invalid_login_response" | tail -n1)
if [ "$invalid_status" = "401" ]; then
    test_success "Invalid password properly rejected"
else
    test_failure "Invalid password was not rejected (HTTP $invalid_status)"
fi

# Test 12: JWT Login with Non-existent User
test_step "JWT login with non-existent user"
nonexistent_login_response=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"nonexistentuser\", \"password\": \"$TEST_PASSWORD\"}" \
    "$BASE_URL/api/auth/login")

nonexistent_status=$(echo "$nonexistent_login_response" | tail -n1)
if [ "$nonexistent_status" = "401" ]; then
    test_success "Non-existent user properly rejected"
else
    test_failure "Non-existent user was not rejected (HTTP $nonexistent_status)"
fi

# Cleanup: Delete test resources
echo -e "\n${BLUE}🧹 Cleanup${NC}"

# Delete created board
if [ -n "$TEST_BOARD_ID" ]; then
    echo "Deleting test board (ID: $TEST_BOARD_ID)..."
    curl -s -X DELETE -H "Authorization: Bearer $JWT_TOKEN" "$BASE_URL/api/boards/$TEST_BOARD_ID" > /dev/null
fi

# Delete created group  
if [ -n "$TEST_GROUP_ID" ]; then
    echo "Deleting test group (ID: $TEST_GROUP_ID)..."
    curl -s -X DELETE -H "Authorization: Bearer $JWT_TOKEN" "$BASE_URL/api/groups/$TEST_GROUP_ID" > /dev/null
fi

# Delete created API key
if [ -n "$CREATED_API_KEY" ]; then
    echo "Deleting created API key..."
    # Get API key ID first
    apikey_list=$(curl -s -H "Authorization: Bearer $JWT_TOKEN" "$BASE_URL/api/api-keys/")
    if echo "$apikey_list" | grep -q "jwt-created-key"; then
        APIKEY_ID=$(echo "$apikey_list" | grep -B5 -A5 "jwt-created-key" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
        if [ -n "$APIKEY_ID" ]; then
            curl -s -X DELETE -H "Authorization: Bearer $JWT_TOKEN" "$BASE_URL/api/api-keys/$APIKEY_ID" > /dev/null
        fi
    fi
fi

# Final Report
echo -e "\n${BLUE}📊 JWT Authentication Test Results${NC}"
echo "=================================================="
echo "Total Tests: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"
echo "Success Rate: $(( PASSED_TESTS * 100 / TOTAL_TESTS ))%"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "\n${GREEN}🎉 All JWT authentication tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}💥 Some JWT authentication tests failed!${NC}"
    exit 1
fi
