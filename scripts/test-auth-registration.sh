#!/bin/bash
"""
User Registration Testing Script for Simple Kanban Board

This script tests the user registration system including:
- Successful user registration
- Duplicate username/email prevention
- Input validation
- Error handling
- Registration edge cases

Usage:
  ./scripts/test-auth-registration.sh
"""

set -e

# Configuration
BASE_URL="${BASE_URL:-https://localhost:8000}"
TEST_BASE="regtest_$(date +%s)"

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

echo -e "${BLUE}📝 User Registration Testing Suite${NC}"
echo "=================================================="
echo "Test Base: $TEST_BASE"
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

# Helper function to test registration
test_registration() {
    local username="$1"
    local email="$2"
    local password="$3"
    local full_name="$4"
    local expected_status="$5"
    local description="$6"
    
    local response=$(curl -s -w "\n%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -d "{\"username\": \"$username\", \"email\": \"$email\", \"password\": \"$password\", \"full_name\": \"$full_name\"}" \
        "$BASE_URL/api/auth/register")
    
    local status_code=$(echo "$response" | tail -n1)
    local body=$(echo "$response" | head -n -1)
    
    if [ "$status_code" = "$expected_status" ]; then
        test_success "$description (HTTP $status_code)"
        if [ "$expected_status" = "201" ] && echo "$body" | grep -q '"id"'; then
            local user_id=$(echo "$body" | grep -o '"id":[0-9]*' | cut -d':' -f2)
            test_info "Created user ID: $user_id"
            echo "$user_id" # Return user ID for cleanup
        fi
        return 0
    else
        test_failure "$description - Expected HTTP $expected_status, got $status_code"
        test_info "Response: $body"
        return 1
    fi
}

# Test 1: Successful User Registration
test_step "Successful user registration"
VALID_USERNAME="${TEST_BASE}_valid"
VALID_EMAIL="${TEST_BASE}_valid@example.com"
# Generate secure random password for testing
VALID_PASSWORD="$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-16)Aa1!"
VALID_FULLNAME="Valid Test User"

CREATED_USER_ID=$(test_registration "$VALID_USERNAME" "$VALID_EMAIL" "$VALID_PASSWORD" "$VALID_FULLNAME" "201" "Valid user registration")

# Test 2: Duplicate Username Prevention
test_step "Duplicate username prevention"
DUPLICATE_EMAIL="${TEST_BASE}_different@example.com"
test_registration "$VALID_USERNAME" "$DUPLICATE_EMAIL" "$VALID_PASSWORD" "Different User" "400" "Duplicate username rejection"

# Test 3: Duplicate Email Prevention
test_step "Duplicate email prevention"
DIFFERENT_USERNAME="${TEST_BASE}_different"
test_registration "$DIFFERENT_USERNAME" "$VALID_EMAIL" "$VALID_PASSWORD" "Different User" "400" "Duplicate email rejection"

# Test 4: Invalid Email Format
test_step "Invalid email format rejection"
INVALID_EMAIL_USER="${TEST_BASE}_invalidemail"
test_registration "$INVALID_EMAIL_USER" "invalid-email-format" "$VALID_PASSWORD" "Invalid Email User" "422" "Invalid email format rejection"

# Test 5: Weak Password Rejection
test_step "Weak password rejection"
WEAK_PASSWORD_USER="${TEST_BASE}_weakpass"
WEAK_PASSWORD_EMAIL="${TEST_BASE}_weakpass@example.com"
test_registration "$WEAK_PASSWORD_USER" "$WEAK_PASSWORD_EMAIL" "weak" "Weak Password User" "422" "Weak password rejection"

# Test 6: Missing Username
test_step "Missing username rejection"
MISSING_USERNAME_EMAIL="${TEST_BASE}_nousername@example.com"
response=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"$MISSING_USERNAME_EMAIL\", \"password\": \"$VALID_PASSWORD\", \"full_name\": \"No Username\"}" \
    "$BASE_URL/api/auth/register")

status_code=$(echo "$response" | tail -n1)
if [ "$status_code" = "422" ]; then
    test_success "Missing username properly rejected (HTTP $status_code)"
else
    test_failure "Missing username not rejected - Expected HTTP 422, got $status_code"
fi

# Test 7: Missing Email
test_step "Missing email rejection"
MISSING_EMAIL_USER="${TEST_BASE}_noemail"
response=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"$MISSING_EMAIL_USER\", \"password\": \"$VALID_PASSWORD\", \"full_name\": \"No Email\"}" \
    "$BASE_URL/api/auth/register")

status_code=$(echo "$response" | tail -n1)
if [ "$status_code" = "422" ]; then
    test_success "Missing email properly rejected (HTTP $status_code)"
else
    test_failure "Missing email not rejected - Expected HTTP 422, got $status_code"
fi

# Test 8: Missing Password
test_step "Missing password rejection"
MISSING_PASSWORD_USER="${TEST_BASE}_nopass"
MISSING_PASSWORD_EMAIL="${TEST_BASE}_nopass@example.com"
response=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"$MISSING_PASSWORD_USER\", \"email\": \"$MISSING_PASSWORD_EMAIL\", \"full_name\": \"No Password\"}" \
    "$BASE_URL/api/auth/register")

status_code=$(echo "$response" | tail -n1)
if [ "$status_code" = "422" ]; then
    test_success "Missing password properly rejected (HTTP $status_code)"
else
    test_failure "Missing password not rejected - Expected HTTP 422, got $status_code"
fi

# Test 9: Empty Request Body
test_step "Empty request body rejection"
response=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Content-Type: application/json" \
    -d "{}" \
    "$BASE_URL/api/auth/register")

status_code=$(echo "$response" | tail -n1)
if [ "$status_code" = "422" ]; then
    test_success "Empty request body properly rejected (HTTP $status_code)"
else
    test_failure "Empty request body not rejected - Expected HTTP 422, got $status_code"
fi

# Test 10: Very Long Username
test_step "Very long username rejection"
LONG_USERNAME=$(printf 'a%.0s' {1..300})  # 300 character username
LONG_USERNAME_EMAIL="${TEST_BASE}_long@example.com"
response=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"$LONG_USERNAME\", \"email\": \"$LONG_USERNAME_EMAIL\", \"password\": \"$VALID_PASSWORD\", \"full_name\": \"Long Username\"}" \
    "$BASE_URL/api/auth/register")

status_code=$(echo "$response" | tail -n1)
if [ "$status_code" = "422" ]; then
    test_success "Very long username properly rejected (HTTP $status_code)"
else
    test_failure "Very long username not rejected - Expected HTTP 422, got $status_code"
fi

# Test 11: Special Characters in Username
test_step "Special characters in username"
SPECIAL_USERNAME="${TEST_BASE}_user@#$%"
SPECIAL_EMAIL="${TEST_BASE}_special@example.com"
response=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"$SPECIAL_USERNAME\", \"email\": \"$SPECIAL_EMAIL\", \"password\": \"$VALID_PASSWORD\", \"full_name\": \"Special User\"}" \
    "$BASE_URL/api/auth/register")

status_code=$(echo "$response" | tail -n1)
# This might be accepted or rejected depending on validation rules
if [ "$status_code" = "201" ] || [ "$status_code" = "422" ]; then
    test_success "Special characters handled appropriately (HTTP $status_code)"
    if [ "$status_code" = "201" ]; then
        test_info "Special characters allowed in username"
    else
        test_info "Special characters rejected in username"
    fi
else
    test_failure "Unexpected response for special characters - HTTP $status_code"
fi

# Test 12: SQL Injection Attempt
test_step "SQL injection attempt in username"
SQL_INJECTION_USERNAME="'; DROP TABLE users; --"
SQL_INJECTION_EMAIL="${TEST_BASE}_sql@example.com"
response=$(curl -s -w "\n%{http_code}" -X POST \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"$SQL_INJECTION_USERNAME\", \"email\": \"$SQL_INJECTION_EMAIL\", \"password\": \"$VALID_PASSWORD\", \"full_name\": \"SQL Injection\"}" \
    "$BASE_URL/api/auth/register")

status_code=$(echo "$response" | tail -n1)
if [ "$status_code" = "422" ] || [ "$status_code" = "400" ]; then
    test_success "SQL injection attempt properly handled (HTTP $status_code)"
else
    test_failure "SQL injection attempt not properly handled - HTTP $status_code"
fi

# Test 13: Verify Created User Can Login
if [ -n "$CREATED_USER_ID" ]; then
    test_step "Verify created user can login"
    login_response=$(curl -s -w "\n%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -d "{\"username\": \"$VALID_USERNAME\", \"password\": \"$VALID_PASSWORD\"}" \
        "$BASE_URL/api/auth/login")
    
    login_status=$(echo "$login_response" | tail -n1)
    login_body=$(echo "$login_response" | head -n -1)
    
    if [ "$login_status" = "200" ] && echo "$login_body" | grep -q '"access_token"'; then
        test_success "Created user can login successfully"
    else
        test_failure "Created user cannot login - HTTP $login_status"
    fi
fi

# Test 14: Registration Response Format Validation
test_step "Registration response format validation"
FORMAT_USERNAME="${TEST_BASE}_format"
FORMAT_EMAIL="${TEST_BASE}_format@example.com"
format_response=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"$FORMAT_USERNAME\", \"email\": \"$FORMAT_EMAIL\", \"password\": \"$VALID_PASSWORD\", \"full_name\": \"Format Test\"}" \
    "$BASE_URL/api/auth/register")

# Check if response contains expected fields
if echo "$format_response" | grep -q '"id"' && \
   echo "$format_response" | grep -q '"username"' && \
   echo "$format_response" | grep -q '"email"' && \
   echo "$format_response" | grep -q '"is_active"' && \
   echo "$format_response" | grep -q '"created_at"'; then
    test_success "Registration response contains all expected fields"
else
    test_failure "Registration response missing expected fields"
    test_info "Response: $format_response"
fi

# Cleanup: Note that we don't delete users as there might not be a delete endpoint
echo -e "\n${BLUE}🧹 Cleanup${NC}"
echo "Note: Created test users remain in system (no user deletion endpoint available)"
if [ -n "$CREATED_USER_ID" ]; then
    echo "Created user ID: $CREATED_USER_ID (username: $VALID_USERNAME)"
fi

# Final Report
echo -e "\n${BLUE}📊 User Registration Test Results${NC}"
echo "=================================================="
echo "Total Tests: $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"
echo "Success Rate: $(( PASSED_TESTS * 100 / TOTAL_TESTS ))%"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "\n${GREEN}🎉 All user registration tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}💥 Some user registration tests failed!${NC}"
    exit 1
fi
