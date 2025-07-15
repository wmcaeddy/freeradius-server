#!/bin/bash
# Test RADIUS authentication with demo tokens

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $*${NC}"
}

success() {
    echo -e "${GREEN}[SUCCESS] $*${NC}"
}

error() {
    echo -e "${RED}[ERROR] $*${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $*${NC}"
}

# Configuration
RADIUS_SERVER=${RADIUS_SERVER:-localhost}
RADIUS_PORT=${RADIUS_PORT:-1812}
RADIUS_SECRET=${RADIUS_SECRET:-testing123}

log "RADIUS Authentication Test"
log "Server: $RADIUS_SERVER:$RADIUS_PORT"
log "Secret: $RADIUS_SECRET"
echo

# Check if radtest is available
if ! command -v radtest &> /dev/null; then
    error "radtest not found. Installing freeradius-utils..."
    apt-get update && apt-get install -y freeradius-utils
fi

# Get current tokens
log "Getting current demo tokens..."
python3 /opt/test-scripts/vasco_token_auth.py

echo
log "Testing RADIUS authentication..."

# Test demo users
declare -A test_users=(
    ["demo"]="$(python3 /opt/test-scripts/vasco_token_auth.py | grep 'demo:' | cut -d':' -f2 | tr -d ' ')"
    ["vasco_demo"]="$(python3 /opt/test-scripts/vasco_token_auth.py | grep 'vasco_demo:' | cut -d':' -f2 | tr -d ' ')"
    ["testuser"]="$(python3 /opt/test-scripts/vasco_token_auth.py | grep 'testuser:' | cut -d':' -f2 | tr -d ' ')"
)

for username in "${!test_users[@]}"; do
    token="${test_users[$username]}"
    
    if [ -n "$token" ]; then
        log "Testing $username with token $token..."
        
        if radtest "$username" "$token" "$RADIUS_SERVER" "$RADIUS_PORT" "$RADIUS_SECRET" > /tmp/radtest_output 2>&1; then
            success "Authentication successful for $username"
            cat /tmp/radtest_output | grep -E "(Access-Accept|Access-Reject)"
        else
            error "Authentication failed for $username"
            cat /tmp/radtest_output
        fi
        echo
    else
        warn "No token found for $username"
    fi
done

log "RADIUS authentication test completed"