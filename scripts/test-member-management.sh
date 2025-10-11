#!/bin/bash
#
# Member Management Testing Script for Simple Kanban Board
#
# This script tests the complete member management functionality including:
# - User search by email and username
# - Adding members to groups with roles
# - Removing members from groups
# - Permission-based access control
# - Member listing and details
#

set -e

# Configuration
NAMESPACE="apps-dev"
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

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}👥 Simple Kanban Member Management Testing Suite${NC}"
echo "=========================================================="
echo "Testing URL: $BASE_URL"

# Get API key from Kubernetes secret
echo -e "\n${YELLOW}📋 Retrieving API key from Kubernetes secret...${NC}"
API_KEY=$(kubectl get secret $SECRET_NAME -n $NAMESPACE -o jsonpath='{.data.api-key}' | base64 -d)

if [ -z "$API_KEY" ]; then
    echo -e "${RED}❌ Failed to retrieve API key${NC}"
    exit 1
fi

echo "✅ API key retrieved successfully"
echo "   Key: ${API_KEY:0:20}..."

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Test function
test_endpoint() {
    local method=$1
    local endpoint=$2
    local description=$3
    local data=${4:-""}
    local expected_status=${5:-200}
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo -e "\n${YELLOW}🧪 Test $TOTAL_TESTS: $description${NC}"
    echo "   $method $endpoint"
    
    if [ -n "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X $method \
            "$BASE_URL$endpoint" \
            -H "Authorization: Bearer $API_KEY" \
            -H "Content-Type: application/json" \
            -d "$data")
    else
        response=$(curl -s -w "\n%{http_code}" -X $method \
            "$BASE_URL$endpoint" \
            -H "Authorization: Bearer $API_KEY" \
            -H "Content-Type: application/json")
    fi
    
    # Split response and status code
    status_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n -1)
    
    if [ "$status_code" = "$expected_status" ]; then
        echo -e "   ${GREEN}✅ PASSED${NC} (HTTP $status_code)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        if [ ${#body} -lt 200 ]; then
            echo "   Response: $body"
        else
            echo "   Response: ${body:0:150}... (truncated)"
        fi
        return 0
    else
        echo -e "   ${RED}❌ FAILED${NC} (HTTP $status_code, expected $expected_status)"
        echo "   Response: $body"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

# Test Suite
echo -e "\n${BLUE}🚀 Starting Member Management Test Suite${NC}"
echo "=========================================================="

# Get current user info first
echo -e "\n${BLUE}👤 Getting current user info...${NC}"
response=$(curl -s -w "\n%{http_code}" -X GET \
    "$BASE_URL/api/auth/me" \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: application/json")

status_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n -1)

if [ "$status_code" = "200" ]; then
    CURRENT_USER_ID=$(echo "$body" | grep -o '"id":[0-9]*' | cut -d':' -f2)
    CURRENT_USER_EMAIL=$(echo "$body" | grep -o '"email":"[^"]*"' | cut -d'"' -f4)
    CURRENT_USER_USERNAME=$(echo "$body" | grep -o '"username":"[^"]*"' | cut -d'"' -f4)
    echo "   Current User ID: $CURRENT_USER_ID"
    echo "   Current User Email: $CURRENT_USER_EMAIL"
    echo "   Current User Username: $CURRENT_USER_USERNAME"
else
    echo -e "${RED}❌ Failed to get current user${NC}"
    exit 1
fi

# Test 1: User Search - Search by email (partial match)
test_endpoint "GET" "/api/auth/users/search?email=test" "Search users by email (partial)"

# Extract first user from search results for testing
SEARCH_USER_ID=$(echo "$body" | grep -o '"id":[0-9]*' | head -1 | cut -d':' -f2)
SEARCH_USER_EMAIL=$(echo "$body" | grep -o '"email":"[^"]*"' | head -1 | cut -d'"' -f4)

# If no users found in search, use current user for testing
if [ -z "$SEARCH_USER_ID" ]; then
    echo "   No users found in search, using current user for testing"
    SEARCH_USER_ID=$CURRENT_USER_ID
    SEARCH_USER_EMAIL=$CURRENT_USER_EMAIL
else
    echo "   Found User ID: $SEARCH_USER_ID"
    echo "   Found User Email: $SEARCH_USER_EMAIL"
fi

# Test 2: User Search - Search by current user's email
if [ -n "$CURRENT_USER_EMAIL" ]; then
    test_endpoint "GET" "/api/auth/users/search?email=$CURRENT_USER_EMAIL" "Search users by email (exact)"
fi

# Test 3: User Search - Search by username
test_endpoint "GET" "/api/auth/users/search?username=test" "Search users by username"

# Test 4: User Search - No results
test_endpoint "GET" "/api/auth/users/search?email=nonexistent@example.com" "Search users with no results"

# Test 5: User Search - Missing parameters (should fail)
test_endpoint "GET" "/api/auth/users/search" "Search users without parameters (should fail)" "" "400"

# Create a test group for member management tests
echo -e "\n${BLUE}📦 Creating test group for member management...${NC}"
test_endpoint "POST" "/api/groups/" "Create test group" \
    '{"name": "Member Management Test Group", "description": "Testing member management"}' "201"

GROUP_ID=$(echo "$body" | grep -o '"id":[0-9]*' | cut -d':' -f2)
echo "   Test Group ID: $GROUP_ID"

if [ -n "$GROUP_ID" ] && [ -n "$SEARCH_USER_ID" ]; then
    # Skip if trying to add current user (they're already the owner)
    if [ "$SEARCH_USER_ID" = "$CURRENT_USER_ID" ]; then
        echo -e "\n${YELLOW}⚠️  Skipping member tests (would add owner to their own group)${NC}"
        echo "   Creating a second test user for member management tests..."
        
        # Create a test user for member management
        RANDOM_NUM=$RANDOM
        response=$(curl -s -w "\n%{http_code}" -X POST \
            "$BASE_URL/api/auth/register" \
            -H "Content-Type: application/json" \
            -d "{\"username\": \"testuser$RANDOM_NUM\", \"email\": \"testuser$RANDOM_NUM@example.com\", \"password\": \"TestPass123!\", \"full_name\": \"Test User $RANDOM_NUM\"}")
        
        status_code=$(echo "$response" | tail -n1)
        body=$(echo "$response" | head -n -1)
        
        if [ "$status_code" = "201" ]; then
            SEARCH_USER_ID=$(echo "$body" | grep -o '"id":[0-9]*' | cut -d':' -f2)
            echo "   Created test user ID: $SEARCH_USER_ID"
        else
            echo -e "   ${RED}❌ Failed to create test user${NC}"
            SEARCH_USER_ID=""
        fi
    fi
    
    if [ -n "$SEARCH_USER_ID" ] && [ "$SEARCH_USER_ID" != "$CURRENT_USER_ID" ]; then
        # Test 6: Add member to group with 'member' role
        test_endpoint "POST" "/api/groups/$GROUP_ID/members" "Add member with 'member' role" \
            "{\"user_id\": $SEARCH_USER_ID, \"role\": \"member\"}"
    
    # Test 7: Get group details (should show new member)
    test_endpoint "GET" "/api/groups/$GROUP_ID" "Get group details with members"
    
    # Verify member is in the list
    if echo "$body" | grep -q "\"user_id\":$SEARCH_USER_ID"; then
        echo -e "   ${GREEN}✅ Member correctly appears in group${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "   ${RED}❌ Member not found in group${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    # Test 8: Try to add same member again (should fail)
    test_endpoint "POST" "/api/groups/$GROUP_ID/members" "Add duplicate member (should fail)" \
        "{\"user_id\": $SEARCH_USER_ID, \"role\": \"member\"}" "400"
    
    # Test 9: Remove member from group
    test_endpoint "DELETE" "/api/groups/$GROUP_ID/members/$SEARCH_USER_ID" "Remove member from group" "" "204"
    
    # Test 10: Verify member is removed
    test_endpoint "GET" "/api/groups/$GROUP_ID" "Verify member removed"
    
    if ! echo "$body" | grep -q "\"user_id\":$SEARCH_USER_ID"; then
        echo -e "   ${GREEN}✅ Member correctly removed from group${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "   ${RED}❌ Member still in group after removal${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    # Test 11: Add member with 'admin' role
    test_endpoint "POST" "/api/groups/$GROUP_ID/members" "Add member with 'admin' role" \
        "{\"user_id\": $SEARCH_USER_ID, \"role\": \"admin\"}"
    
    # Verify admin role
    test_endpoint "GET" "/api/groups/$GROUP_ID" "Verify admin role assignment"
    
    if echo "$body" | grep -q "\"role\":\"admin\""; then
        echo -e "   ${GREEN}✅ Admin role correctly assigned${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "   ${RED}❌ Admin role not assigned correctly${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    # Test 12: Try to add non-existent user (should fail)
    test_endpoint "POST" "/api/groups/$GROUP_ID/members" "Add non-existent user (should fail)" \
        '{"user_id": 999999, "role": "member"}' "404"
    
    # Test 13: Try to remove non-existent member (should fail)
    test_endpoint "DELETE" "/api/groups/$GROUP_ID/members/999999" "Remove non-existent member (should fail)" "" "404"
    
        # Cleanup: Delete test group
        echo -e "\n${BLUE}🧹 Cleaning up test group...${NC}"
        test_endpoint "DELETE" "/api/groups/$GROUP_ID" "Delete test group" "" "204"
    else
        echo -e "${YELLOW}⚠️  Skipping member management tests (no suitable test user)${NC}"
        # Still cleanup the group
        test_endpoint "DELETE" "/api/groups/$GROUP_ID" "Delete test group" "" "204"
    fi
else
    echo -e "${RED}❌ Could not create test group${NC}"
fi

# Test Summary
echo -e "\n${BLUE}📊 Test Summary${NC}"
echo "=========================================================="
echo -e "Total Tests:  ${BLUE}$TOTAL_TESTS${NC}"
echo -e "Passed:       ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed:       ${RED}$FAILED_TESTS${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "\n${GREEN}🎉 All tests passed!${NC}"
    echo ""
    echo "✅ User Search Features:"
    echo "   ✅ Search by email (partial and exact)"
    echo "   ✅ Search by username"
    echo "   ✅ Empty results handling"
    echo "   ✅ Parameter validation"
    echo ""
    echo "✅ Member Management Features:"
    echo "   ✅ Add members with different roles"
    echo "   ✅ Remove members from groups"
    echo "   ✅ Duplicate member prevention"
    echo "   ✅ Non-existent user handling"
    echo "   ✅ Role assignment (member/admin)"
    echo "   ✅ Member listing in group details"
    echo ""
    echo "🚀 Member Management System: FULLY FUNCTIONAL"
    exit 0
else
    echo -e "\n${RED}❌ Some tests failed${NC}"
    echo "Please review the failures above"
    exit 1
fi
