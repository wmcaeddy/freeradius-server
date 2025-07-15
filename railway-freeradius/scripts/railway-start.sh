#!/bin/bash
# Railway.com startup script for FreeRADIUS + PrivacyIDEA

set -e

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

log "Starting Railway.com FreeRADIUS + Simple Token Auth deployment..."

# Ensure data directory exists
mkdir -p /app/data

# Start Redis (for future use)
log "Starting Redis server..."
redis-server --daemonize yes --port 6379

# Start simple web interface
log "Starting simple web interface..."
nginx &

# Initialize token database (done automatically by the Python module)
log "Token database will be initialized automatically"

# Configure FreeRADIUS
log "Configuring FreeRADIUS..."
chown -R freerad:freerad /etc/freeradius /app/data /var/log/freeradius /var/run/freeradius

# Enable required modules
cd /etc/freeradius/3.0/mods-enabled
ln -sf ../mods-available/privacyidea simple_token_auth 2>/dev/null || true
ln -sf ../mods-available/python3 python3 2>/dev/null || true

# Enable sites
cd /etc/freeradius/3.0/sites-enabled
ln -sf ../sites-available/privacyidea token_auth 2>/dev/null || true

# Test configuration
log "Testing FreeRADIUS configuration..."
runuser -u freerad -- freeradius -C -d /etc/freeradius/3.0

# Start FreeRADIUS
log "Starting FreeRADIUS..."
exec runuser -u freerad -- freeradius -f -d /etc/freeradius/3.0