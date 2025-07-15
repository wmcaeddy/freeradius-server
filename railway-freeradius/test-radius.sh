#!/bin/bash
# Test script for FreeRADIUS deployment with PrivacyIDEA

set -e

echo "=== FreeRADIUS + PrivacyIDEA Test Script ==="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
RADIUS_HOST="${RADIUS_HOST:-localhost}"
RADIUS_SECRET="${RADIUS_SECRET:-testing123}"
PROXY_PORT="${PROXY_PORT:-11812}"
DIRECT_PORT="${DIRECT_PORT:-1812}"
PRIVACYIDEA_URL="${PRIVACYIDEA_URL:-http://localhost:80}"

# Function to test RADIUS authentication
test_auth() {
    local user=$1
    local pass=$2
    local port=$3
    local desc=$4
    
    echo -n "Testing $desc... "
    
    if radtest "$user" "$pass" "$RADIUS_HOST" 0 "$RADIUS_SECRET" -P "$port" > /dev/null 2>&1; then
        echo -e "${GREEN}PASS${NC}"
        return 0
    else
        echo -e "${RED}FAIL${NC}"
        return 1
    fi
}

# Check if radtest is available
if ! command -v radtest &> /dev/null; then
    echo -e "${RED}Error: radtest command not found${NC}"
    echo "Please install freeradius-utils:"
    echo "  Ubuntu/Debian: apt-get install freeradius-utils"
    echo "  RHEL/CentOS: yum install freeradius-utils"
    exit 1
fi

# Check PrivacyIDEA health
echo -e "${BLUE}0. Checking PrivacyIDEA server health...${NC}"
if curl -s -f "$PRIVACYIDEA_URL/health" > /dev/null; then
    echo -e "${GREEN}PrivacyIDEA server is running${NC}"
else
    echo -e "${RED}PrivacyIDEA server is not accessible${NC}"
    echo "Make sure the server is running: docker-compose up -d privacyidea"
    echo "Or check the URL: $PRIVACYIDEA_URL"
fi

echo

# Test direct authentication to PrivacyIDEA instance
echo "1. Testing direct authentication (port $DIRECT_PORT):"
echo -e "${YELLOW}Note: These tests require demo tokens to be set up first${NC}"
echo "Run: docker-compose exec privacyidea python3 /opt/privacyidea/setup-demo-tokens.py"
echo
test_auth "demo" "755224" "$DIRECT_PORT" "Demo user with HOTP token"
test_auth "vasco_demo" "123456" "$DIRECT_PORT" "Vasco demo token"
test_auth "testuser" "287082" "$DIRECT_PORT" "Test user with HOTP token"

echo

# Test proxy authentication
echo "2. Testing proxy authentication (port $PROXY_PORT):"
test_auth "demo" "755224" "$PROXY_PORT" "Demo user via proxy"
test_auth "vasco_demo" "123456" "$PROXY_PORT" "Vasco demo token via proxy"

echo

# Test PrivacyIDEA Web UI
echo "3. Testing PrivacyIDEA Web UI:"
echo -e "${BLUE}PrivacyIDEA Web Interface:${NC} $PRIVACYIDEA_URL"
echo "Default admin credentials: admin / admin (change in production!)"
echo

# Test failover scenario
echo "4. Testing failover scenario:"
echo -e "${YELLOW}Note: This requires manual intervention to stop one backend${NC}"
echo "You can stop the primary backend with:"
echo "  docker-compose stop freeradius-privacyidea"
echo "Then run this script again to verify failover works"

echo
echo "=== Test Summary ==="
echo "PrivacyIDEA Web UI: $PRIVACYIDEA_URL"
echo "Direct authentication endpoint: $RADIUS_HOST:$DIRECT_PORT"
echo "Proxy authentication endpoint: $RADIUS_HOST:$PROXY_PORT"
echo "Shared secret: $RADIUS_SECRET"
echo
echo "=== Demo Token Information ==="
echo "Demo users created during initialization:"
echo "  - demo: HOTP/TOTP tokens (use OTP values from authenticator)"
echo "  - vasco_demo: Vasco demo token"
echo "  - testuser: HOTP token"
echo
echo "To generate OTP values:"
echo "  - Use Google Authenticator or similar for TOTP"
echo "  - Use the secret: 3132333435363738393031323334353637383930"
echo "  - Or check PrivacyIDEA web interface for current values"