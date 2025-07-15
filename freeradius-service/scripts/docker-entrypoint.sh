#!/bin/bash
# FreeRADIUS Service Entry Point for Railway.com

set -e

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] FREERADIUS: $*"
}

log "Starting FreeRADIUS service..."

# Ensure data directory exists
mkdir -p /app/data/freeradius

# Set permissions
chown -R freerad:freerad /app/data /var/log/freeradius /etc/freeradius /var/run/freeradius

# Wait for PrivacyIDEA service to be ready
if [ -n "$PRIVACYIDEA_URL" ]; then
    log "Waiting for PrivacyIDEA service to be ready..."
    for i in {1..30}; do
        if curl -f "${PRIVACYIDEA_URL}/health" > /dev/null 2>&1; then
            log "PrivacyIDEA service is ready"
            break
        fi
        log "Waiting for PrivacyIDEA service... ($i/30)"
        sleep 10
    done
fi

# Enable required modules
cd /etc/freeradius/3.0/mods-enabled
ln -sf ../mods-available/privacyidea_client privacyidea_client 2>/dev/null || true
ln -sf ../mods-available/python3 python3 2>/dev/null || true
ln -sf ../mods-available/linelog linelog 2>/dev/null || true
ln -sf ../mods-available/detail detail 2>/dev/null || true
ln -sf ../mods-available/preprocess preprocess 2>/dev/null || true
ln -sf ../mods-available/acct_unique acct_unique 2>/dev/null || true

# Enable sites
cd /etc/freeradius/3.0/sites-enabled
rm -f default inner-tunnel 2>/dev/null || true
ln -sf ../sites-available/default default 2>/dev/null || true

# Test configuration
log "Testing FreeRADIUS configuration..."
if ! runuser -u freerad -- freeradius -C -d /etc/freeradius/3.0; then
    log "FreeRADIUS configuration test failed"
    exit 1
fi

log "FreeRADIUS configuration test passed"

# Start FreeRADIUS
log "Starting FreeRADIUS server..."
exec runuser -u freerad -- "$@"