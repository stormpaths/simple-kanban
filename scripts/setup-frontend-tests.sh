#!/bin/bash
"""
Setup Frontend Tests

This script prepares the frontend test environment by:
1. Creating a test user if needed
2. Saving credentials for docker-compose
3. Verifying the setup

Usage:
    ./scripts/setup-frontend-tests.sh [--base-url URL] [--force]
"""

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FRONTEND_TEST_DIR="$PROJECT_ROOT/tests/frontend"
BASE_URL="${BASE_URL:-https://kanban.stormpath.dev}"
FORCE_CREATE=false

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --base-url)
            BASE_URL="$2"
            shift 2
            ;;
        --force)
            FORCE_CREATE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [--base-url URL] [--force]"
            echo ""
            echo "Options:"
            echo "  --base-url URL    Base URL of the application (default: https://kanban.stormpath.dev)"
            echo "  --force           Force creation of new test user even if credentials exist"
            echo "  --help            Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🎭 Frontend Test Setup${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Check if credentials already exist
CRED_FILE="$FRONTEND_TEST_DIR/test-credentials.env"
if [ -f "$CRED_FILE" ] && [ "$FORCE_CREATE" = false ]; then
    echo -e "${GREEN}✅ Test credentials already exist${NC}"
    echo -e "${BLUE}ℹ️  Location: $CRED_FILE${NC}"
    echo ""
    
    # Source and display existing credentials
    source "$CRED_FILE"
    echo -e "${BLUE}📝 Current credentials:${NC}"
    echo -e "   Email:    $TEST_USERNAME"
    echo -e "   Password: $TEST_PASSWORD"
    echo ""
    
    # Ask if user wants to continue
    read -p "Use existing credentials? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}✅ Using existing credentials${NC}"
        exit 0
    else
        echo -e "${YELLOW}⚠️  Creating new credentials...${NC}"
        FORCE_CREATE=true
    fi
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is required but not installed${NC}"
    exit 1
fi

# Check if requests library is available
if ! python3 -c "import requests" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Installing required Python packages...${NC}"
    pip3 install requests --quiet || {
        echo -e "${RED}❌ Failed to install requests library${NC}"
        exit 1
    }
fi

# Run the setup script
echo -e "${BLUE}🔧 Creating test user...${NC}"
echo ""

cd "$FRONTEND_TEST_DIR"
python3 setup_test_user.py \
    --base-url "$BASE_URL" \
    --output-dir "$FRONTEND_TEST_DIR" \
    --verify

if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}❌ Failed to create test user${NC}"
    exit 1
fi

# Update docker-compose.yml with new credentials
echo ""
echo -e "${BLUE}🔧 Updating docker-compose.yml...${NC}"

source "$CRED_FILE"

# Create a backup
cp docker-compose.yml docker-compose.yml.bak

# Update the TEST_USERNAME line
sed -i "s|TEST_USERNAME=\${TEST_USERNAME:-.*}|TEST_USERNAME=\${TEST_USERNAME:-$TEST_USERNAME}|g" docker-compose.yml

echo -e "${GREEN}✅ docker-compose.yml updated${NC}"
echo -e "${BLUE}ℹ️  Backup saved to: docker-compose.yml.bak${NC}"

# Display summary
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Frontend test setup complete!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}📝 Next steps:${NC}"
echo ""
echo -e "  1. Run tests with credentials:"
echo -e "     ${YELLOW}cd tests/frontend && docker-compose run --rm frontend-tests${NC}"
echo ""
echo -e "  2. Or source credentials for manual testing:"
echo -e "     ${YELLOW}source tests/frontend/test-credentials.env${NC}"
echo ""
echo -e "  3. Run full test suite:"
echo -e "     ${YELLOW}./scripts/test-all.sh${NC}"
echo ""
echo -e "${BLUE}🔑 Credentials saved to:${NC}"
echo -e "   - $FRONTEND_TEST_DIR/test-credentials.env"
echo -e "   - $FRONTEND_TEST_DIR/.env.test"
echo -e "   - $FRONTEND_TEST_DIR/test_credentials.py"
echo -e "   - $FRONTEND_TEST_DIR/test-credentials.json"
echo ""
