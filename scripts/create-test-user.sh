#!/bin/bash
"""
Create Test User Script for Simple Kanban Board

This script creates a new test user and generates an API key for testing purposes.
"""

set -e

# Configuration
BASE_URL="https://kanban.stormpath.dev"
ADMIN_API_KEY=$(kubectl get secret simple-kanban-test-api-key -n apps-dev -o jsonpath='{.data.api-key}' | base64 -d)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}👤 Simple Kanban Test User Creation${NC}"
echo "=============================================="

# Generate random test user data
TIMESTAMP=$(date +%s)
TEST_USERNAME="testuser_$TIMESTAMP"
TEST_EMAIL="test_$TIMESTAMP@example.com"
TEST_PASSWORD="TestPassword123!"

echo -e "\n${YELLOW}📋 Creating new test user...${NC}"
echo "   Username: $TEST_USERNAME"
echo "   Email: $TEST_EMAIL"
echo "   Password: $TEST_PASSWORD"

# Create the test user
echo -e "\n${YELLOW}🔨 Registering user...${NC}"
register_response=$(curl -s -w "\n%{http_code}" -X POST \
    "$BASE_URL/api/auth/register" \
    -H "Content-Type: application/json" \
    -d "{
        \"username\": \"$TEST_USERNAME\",
        \"email\": \"$TEST_EMAIL\",
        \"password\": \"$TEST_PASSWORD\",
        \"full_name\": \"Test User $TIMESTAMP\"
    }")

register_status=$(echo "$register_response" | tail -n1)
register_body=$(echo "$register_response" | head -n -1)

if [ "$register_status" = "201" ]; then
    echo -e "   ${GREEN}✅ User created successfully${NC}"
    user_id=$(echo "$register_body" | grep -o '"id":[0-9]*' | cut -d':' -f2)
    echo "   User ID: $user_id"
else
    echo -e "   ${RED}❌ Failed to create user${NC} (HTTP $register_status)"
    echo "   Response: $register_body"
    exit 1
fi

# Login to get JWT token
echo -e "\n${YELLOW}🔑 Logging in to get JWT token...${NC}"
login_response=$(curl -s -w "\n%{http_code}" -X POST \
    "$BASE_URL/api/auth/login" \
    -H "Content-Type: application/json" \
    -d "{
        \"username\": \"$TEST_USERNAME\",
        \"password\": \"$TEST_PASSWORD\"
    }")

login_status=$(echo "$login_response" | tail -n1)
login_body=$(echo "$login_response" | head -n -1)

if [ "$login_status" = "200" ]; then
    echo -e "   ${GREEN}✅ Login successful${NC}"
    jwt_token=$(echo "$login_body" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    echo "   JWT Token: ${jwt_token:0:20}..."
else
    echo -e "   ${RED}❌ Failed to login${NC} (HTTP $login_status)"
    echo "   Response: $login_body"
    exit 1
fi

# Create API key for the test user
echo -e "\n${YELLOW}🗝️  Creating API key for test user...${NC}"
api_key_response=$(curl -s -w "\n%{http_code}" -X POST \
    "$BASE_URL/api/api-keys/" \
    -H "Authorization: Bearer $jwt_token" \
    -H "Content-Type: application/json" \
    -d "{
        \"name\": \"test-user-key-$TIMESTAMP\",
        \"description\": \"API key for test user $TEST_USERNAME\",
        \"scopes\": [\"read\", \"write\"],
        \"expires_in_days\": 30
    }")

api_key_status=$(echo "$api_key_response" | tail -n1)
api_key_body=$(echo "$api_key_response" | head -n -1)

if [ "$api_key_status" = "201" ]; then
    echo -e "   ${GREEN}✅ API key created successfully${NC}"
    
    # Extract API key and details
    api_key=$(echo "$api_key_body" | grep -o '"api_key":"[^"]*' | cut -d'"' -f4)
    key_id=$(echo "$api_key_body" | grep -o '"id":[0-9]*' | cut -d':' -f2)
    key_prefix=$(echo "$api_key_body" | grep -o '"key_prefix":"[^"]*' | cut -d'"' -f4)
    
    echo "   API Key: ${api_key:0:20}..."
    echo "   Key ID: $key_id"
    echo "   Key Prefix: $key_prefix"
else
    echo -e "   ${RED}❌ Failed to create API key${NC} (HTTP $api_key_status)"
    echo "   Response: $api_key_body"
    exit 1
fi

# Test the new API key
echo -e "\n${YELLOW}🧪 Testing new API key...${NC}"
test_response=$(curl -s -w "\n%{http_code}" -X GET \
    "$BASE_URL/api/boards/" \
    -H "Authorization: Bearer $api_key" \
    -H "Content-Type: application/json")

test_status=$(echo "$test_response" | tail -n1)
test_body=$(echo "$test_response" | head -n -1)

if [ "$test_status" = "200" ]; then
    echo -e "   ${GREEN}✅ API key authentication successful${NC}"
    board_count=$(echo "$test_body" | grep -o '"id":' | wc -l)
    echo "   Accessible boards: $board_count"
else
    echo -e "   ${RED}❌ API key authentication failed${NC} (HTTP $test_status)"
    echo "   Response: $test_body"
fi

# Create Kubernetes secret for the new test user
echo -e "\n${YELLOW}☸️  Creating Kubernetes secret...${NC}"
secret_name="simple-kanban-test-user-$user_id"

kubectl create secret generic "$secret_name" -n apps-dev \
    --from-literal=api-key="$api_key" \
    --from-literal=key-name="test-user-key-$TIMESTAMP" \
    --from-literal=user-id="$user_id" \
    --from-literal=username="$TEST_USERNAME" \
    --from-literal=email="$TEST_EMAIL" \
    --from-literal=password="$TEST_PASSWORD" \
    --from-literal=jwt-token="$jwt_token" \
    --from-literal=scopes="read,write" 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "   ${GREEN}✅ Kubernetes secret created${NC}"
    echo "   Secret name: $secret_name"
else
    echo -e "   ${YELLOW}⚠️  Secret may already exist or creation failed${NC}"
fi

echo -e "\n${BLUE}📊 Test User Summary${NC}"
echo "=============================================="
echo "✅ User Created: $TEST_USERNAME (ID: $user_id)"
echo "✅ JWT Token: Generated and working"
echo "✅ API Key: Generated and working"
echo "✅ Kubernetes Secret: $secret_name"

echo -e "\n${GREEN}🎉 Test user created successfully!${NC}"
echo ""
echo "📝 Test User Details:"
echo "   Username: $TEST_USERNAME"
echo "   Email: $TEST_EMAIL"
echo "   Password: $TEST_PASSWORD"
echo "   User ID: $user_id"
echo "   API Key: ${api_key:0:20}..."
echo "   Secret: apps-dev/$secret_name"
echo ""
echo "🧪 Test the API key:"
echo "   curl -H \"Authorization: Bearer $api_key\" \\"
echo "        $BASE_URL/api/boards/"
echo ""
echo "🗑️  Cleanup (when done testing):"
echo "   kubectl delete secret $secret_name -n apps-dev"
