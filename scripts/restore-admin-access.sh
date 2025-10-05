#!/bin/bash
# Restore Admin Access Script
#
# This script helps restore admin access for a user account
# Usage: ./scripts/restore-admin-access.sh <email>

set -e

# Configuration
BASE_URL="${BASE_URL:-https://kanban.stormpath.dev}"

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

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check if email provided
if [ -z "$1" ]; then
    echo "Usage: $0 <email>"
    echo "Example: $0 michaelarichard@gmail.com"
    exit 1
fi

USER_EMAIL="$1"

echo -e "${BLUE}🔧 Admin Access Restoration${NC}"
echo "=================================="
echo "Email: $USER_EMAIL"
echo "Base URL: $BASE_URL"
echo ""

log_info "This script will help you restore admin access for your account."
echo ""

# Method 1: Try to login and check current status
log_info "Method 1: Login and check current status"
echo "Please provide your password to check your current account status:"
echo ""
echo "curl -X POST '$BASE_URL/api/auth/login' \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"username\": \"$USER_EMAIL\", \"password\": \"YOUR_PASSWORD\"}'"
echo ""

# Method 2: Database restoration via kubectl
log_info "Method 2: Direct database restoration (requires kubectl access)"
echo ""
echo "If you have kubectl access, you can restore admin privileges directly:"
echo ""
echo "# Connect to the database pod"
echo "kubectl exec -it \$(kubectl get pods -n apps-dev -l app=postgresql -o jsonpath='{.items[0].metadata.name}') -n apps-dev -- psql -U postgres -d kanban"
echo ""
echo "# Then run this SQL command:"
echo "UPDATE users SET is_admin = true, is_active = true WHERE email = '$USER_EMAIL';"
echo ""

# Method 3: Create a new admin user
log_info "Method 3: Create a temporary admin user"
echo ""
echo "You can create a new admin user and then restore your original account:"
echo ""
echo "1. Register a new user via the web interface"
echo "2. Use kubectl to make that user an admin:"
echo "   kubectl exec -it \$(kubectl get pods -n apps-dev -l app=postgresql -o jsonpath='{.items[0].metadata.name}') -n apps-dev -- psql -U postgres -d kanban -c \"UPDATE users SET is_admin = true WHERE email = 'new_admin@example.com';\""
echo "3. Login with the new admin user and restore your original account"
echo ""

# Method 4: Bootstrap admin user
log_info "Method 4: Use bootstrap system to create admin user"
echo ""
echo "The bootstrap system we created can make a user admin:"
echo ""
echo "1. Run: ./scripts/test-bootstrap.sh --cleanup-only"
echo "2. Run: ./scripts/test-bootstrap.sh"
echo "3. The bootstrap user will have admin privileges"
echo "4. Use that user to restore your original account"
echo ""

log_warning "IMPORTANT: If you accidentally disabled your own account, you'll need database access to restore it."
echo ""

# Check if we can determine the issue
log_info "Diagnostic: Testing login endpoint availability"
health_response=$(curl -s -w "%{http_code}" "$BASE_URL/health" -o /dev/null 2>/dev/null || echo "ERROR")

if [ "$health_response" = "200" ]; then
    log_success "Application is responding normally"
    
    # Test if we can access the login endpoint
    login_test=$(curl -s -w "\n%{http_code}" -X POST \
        -H "Content-Type: application/json" \
        -d '{"username": "test", "password": "test"}' \
        "$BASE_URL/api/auth/login" 2>/dev/null)
    
    login_status=$(echo "$login_test" | tail -n1)
    if [ "$login_status" = "401" ]; then
        log_success "Login endpoint is working (returned 401 for invalid credentials)"
        echo ""
        log_info "Your account status issue is likely one of:"
        echo "  1. Account was disabled (is_active = false)"
        echo "  2. Admin privileges were removed (is_admin = false)"
        echo "  3. Session expired and needs re-login"
        echo ""
        log_info "Try logging in again with your credentials first."
    else
        log_warning "Login endpoint returned unexpected status: $login_status"
    fi
else
    log_failure "Application health check failed (HTTP $health_response)"
fi

echo ""
echo -e "${BLUE}📋 Recommended Steps:${NC}"
echo "1. Try logging in again with your credentials"
echo "2. If login fails, use Method 2 (database access) to restore your account"
echo "3. If no database access, use Method 4 (bootstrap admin) as backup"
echo ""
echo -e "${GREEN}Need immediate help? The bootstrap system can create an admin user:${NC}"
echo "  ./scripts/test-bootstrap.sh"
