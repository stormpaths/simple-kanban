#!/bin/bash
# Check User Admin Status Script
#
# This script checks if a specific user has admin privileges
# Usage: ./scripts/check-user-admin.sh <email>

set -e

# Configuration
BASE_URL="${BASE_URL:-https://kanban.stormpath.dev}"
NAMESPACE="apps-dev"
SECRET_NAME="simple-kanban-test-api-key"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_failure() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if email provided
if [ -z "$1" ]; then
    echo "Usage: $0 <email>"
    echo "Example: $0 michaelarichard@gmail.com"
    exit 1
fi

USER_EMAIL="$1"

echo -e "${BLUE}🔍 User Admin Status Check${NC}"
echo "=================================="
echo "Email: $USER_EMAIL"
echo "Base URL: $BASE_URL"
echo ""

# Get API key from secret
log_info "Getting API key from Kubernetes secret..."
if ! kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" >/dev/null 2>&1; then
    log_failure "API key secret not found. Run bootstrap first:"
    echo "  ./scripts/test-bootstrap.sh"
    exit 1
fi

API_KEY=$(kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" -o jsonpath='{.data.api-key}' | base64 -d)
if [ -z "$API_KEY" ]; then
    log_failure "Could not retrieve API key from secret"
    exit 1
fi

log_success "API key retrieved"

# Try to get user profile through different methods
log_info "Attempting to find user information..."

# Method 1: Try to get all users (if we have admin access)
echo ""
echo "Method 1: Checking admin user list..."
admin_response=$(curl -s -w "\n%{http_code}" -X GET \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: application/json" \
    "$BASE_URL/api/admin/users")

admin_status=$(echo "$admin_response" | tail -n1)
admin_body=$(echo "$admin_response" | head -n -1)

if [ "$admin_status" = "200" ]; then
    log_success "Admin access available - checking user list"
    
    # Check if the user exists in the admin list
    if echo "$admin_body" | grep -q "$USER_EMAIL"; then
        echo ""
        log_success "User found in system!"
        
        # Extract user details
        user_info=$(echo "$admin_body" | jq -r ".users[] | select(.email == \"$USER_EMAIL\")")
        
        if [ -n "$user_info" ]; then
            echo ""
            echo -e "${BLUE}📋 User Details:${NC}"
            echo "$user_info" | jq '{
                id: .id,
                username: .username,
                email: .email,
                full_name: .full_name,
                is_admin: .is_admin,
                is_active: .is_active,
                is_verified: .is_verified,
                created_at: .created_at
            }'
            
            is_admin=$(echo "$user_info" | jq -r '.is_admin')
            if [ "$is_admin" = "true" ]; then
                echo ""
                log_success "✨ USER HAS ADMIN PRIVILEGES ✨"
            else
                echo ""
                log_info "User does not have admin privileges"
            fi
        else
            log_failure "Could not extract user details"
        fi
    else
        log_info "User not found in admin user list"
    fi
else
    log_info "No admin access with current API key (HTTP $admin_status)"
    
    # Method 2: Try to login and check profile (would need password)
    echo ""
    echo "Method 2: Direct login check (requires password)..."
    log_info "To check admin status via login, you would need to:"
    echo "  1. Login with your credentials"
    echo "  2. Check your profile endpoint"
    echo ""
    echo "Example:"
    echo "  curl -X POST '$BASE_URL/api/auth/login' \\"
    echo "    -H 'Content-Type: application/json' \\"
    echo "    -d '{\"username\": \"$USER_EMAIL\", \"password\": \"YOUR_PASSWORD\"}'"
fi

# Method 3: Try to access admin endpoints to see if user has admin JWT
echo ""
echo "Method 3: Database query (if available)..."
log_info "For direct database access, you could run:"
echo "  kubectl exec -it deployment/simple-kanban-backend -n apps-dev -- \\"
echo "    python -c \"
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check_user():
    engine = create_async_engine(os.getenv('DATABASE_URL'))
    async with engine.begin() as conn:
        result = await conn.execute(
            text('SELECT id, username, email, full_name, is_admin, is_active FROM users WHERE email = :email'),
            {'email': '$USER_EMAIL'}
        )
        user = result.fetchone()
        if user:
            print(f'User found: {dict(user)}')
            print(f'Admin status: {user.is_admin}')
        else:
            print('User not found')

asyncio.run(check_user())
\""

echo ""
echo -e "${BLUE}📊 Summary${NC}"
echo "=================================="
if [ "$admin_status" = "200" ]; then
    echo "✅ Admin API access: Available"
    if echo "$admin_body" | grep -q "$USER_EMAIL"; then
        echo "✅ User found: Yes"
        user_info=$(echo "$admin_body" | jq -r ".users[] | select(.email == \"$USER_EMAIL\")")
        is_admin=$(echo "$user_info" | jq -r '.is_admin')
        if [ "$is_admin" = "true" ]; then
            echo "✅ Admin status: YES - USER IS ADMIN"
        else
            echo "❌ Admin status: NO - User is not admin"
        fi
    else
        echo "❌ User found: No"
    fi
else
    echo "❌ Admin API access: Not available"
    echo "ℹ️  Alternative methods available (see above)"
fi
