#!/bin/bash
# Deploy separated FreeRADIUS and PrivacyIDEA services to Railway.com

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

error() {
    echo -e "${RED}[ERROR] $*${NC}"
}

success() {
    echo -e "${GREEN}[SUCCESS] $*${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $*${NC}"
}

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    error "Railway CLI is not installed. Please install it first:"
    echo "curl -fsSL https://railway.com/install.sh | sh"
    exit 1
fi

# Check if user is logged in
if ! railway whoami &> /dev/null; then
    error "You are not logged in to Railway. Please run:"
    echo "railway login"
    exit 1
fi

log "Starting deployment of separated FreeRADIUS and PrivacyIDEA services..."

# Function to create and deploy a service
deploy_service() {
    local service_name=$1
    local service_dir=$2
    local description=$3
    
    log "Deploying $description..."
    
    # Create new Railway project for the service
    log "Creating Railway project for $service_name..."
    
    # Navigate to service directory
    cd "$service_dir"
    
    # Check if railway.toml exists
    if [ ! -f "railway.toml" ]; then
        error "railway.toml not found in $service_dir"
        return 1
    fi
    
    # Deploy the service
    log "Deploying $service_name to Railway..."
    railway up --detach || {
        error "Failed to deploy $service_name"
        return 1
    }
    
    # Get the service URL
    local service_url=$(railway status --json | jq -r '.services.edges[0].node.serviceInstances.edges[0].node.deployments.edges[0].node.url // "Not available"')
    
    success "$description deployed successfully!"
    log "Service URL: $service_url"
    
    # Return to root directory
    cd ..
    
    return 0
}

# Deploy PrivacyIDEA service first
log "=== Deploying PrivacyIDEA Service ==="
deploy_service "privacyidea" "privacyidea-service" "PrivacyIDEA Authentication Service"

# Get PrivacyIDEA service URL for FreeRADIUS configuration
log "Getting PrivacyIDEA service URL..."
cd privacyidea-service
PRIVACYIDEA_URL=$(railway status --json | jq -r '.services.edges[0].node.serviceInstances.edges[0].node.deployments.edges[0].node.url // ""')
cd ..

if [ -z "$PRIVACYIDEA_URL" ]; then
    warn "Could not retrieve PrivacyIDEA URL automatically. You'll need to set it manually."
    PRIVACYIDEA_URL="https://your-privacyidea-service.railway.app"
fi

log "PrivacyIDEA URL: $PRIVACYIDEA_URL"

# Deploy FreeRADIUS service
log "=== Deploying FreeRADIUS Service ==="
log "Setting PRIVACYIDEA_URL environment variable..."

# Set environment variable for FreeRADIUS service
cd freeradius-service
railway variables set PRIVACYIDEA_URL="$PRIVACYIDEA_URL"

deploy_service "freeradius" "freeradius-service" "FreeRADIUS Authentication Server"

# Get FreeRADIUS service URL
FREERADIUS_URL=$(railway status --json | jq -r '.services.edges[0].node.serviceInstances.edges[0].node.deployments.edges[0].node.url // "Not available"')
cd ..

log "=== Deployment Summary ==="
success "Both services deployed successfully!"
echo
log "PrivacyIDEA Web Interface: $PRIVACYIDEA_URL"
log "FreeRADIUS RADIUS Server: $FREERADIUS_URL (ports 1812/1813)"
echo
log "Next steps:"
echo "1. Configure environment variables in Railway dashboard"
echo "2. Set up demo tokens in PrivacyIDEA"
echo "3. Test RADIUS authentication"
echo
log "Environment variables to set:"
echo "PrivacyIDEA Service:"
echo "  - PI_SECRET_KEY"
echo "  - PI_PEPPER"
echo "  - PI_ADMIN_PASSWORD"
echo
echo "FreeRADIUS Service:"
echo "  - PRIVACYIDEA_URL (already set to: $PRIVACYIDEA_URL)"
echo "  - RADIUS_CLIENT_SECRET"
echo
success "Deployment complete!"