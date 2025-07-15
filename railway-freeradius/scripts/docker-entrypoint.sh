#!/bin/bash
set -e

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

# Check if we're running as root and need to drop privileges
if [ "$(id -u)" = "0" ]; then
    log "Running as root, setting up permissions..."
    chown -R freerad:freerad /app/data /var/log/radius /var/run/radiusd
    exec gosu freerad "$0" "$@"
fi

# Ensure data directory exists and has correct permissions
if [ ! -d "/app/data" ]; then
    log "Creating data directory..."
    mkdir -p /app/data
fi

# Copy default certificates if they don't exist
if [ ! -f "/app/data/certs/server.pem" ]; then
    log "Generating default certificates..."
    mkdir -p /app/data/certs
    cd /app/data/certs
    
    # Generate CA certificate
    openssl req -new -x509 -keyout ca.key -out ca.pem -days 3650 -nodes \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=FreeRADIUS-CA"
    
    # Generate server certificate
    openssl req -new -keyout server.key -out server.csr -nodes \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=radius.local"
    openssl x509 -req -in server.csr -CA ca.pem -CAkey ca.key -CAcreateserial \
        -out server.pem -days 365 -extensions v3_req
    
    # Set permissions
    chmod 640 *.key *.pem
    cd -
fi

# Link certificates to expected location
ln -sf /app/data/certs /usr/local/etc/raddb/certs

# Check environment variables for PrivacyIDEA configuration
if [ -n "$PRIVACYIDEA_URL" ]; then
    log "Configuring PrivacyIDEA URL: $PRIVACYIDEA_URL"
    sed -i "s|PRIVACYIDEA_URL|$PRIVACYIDEA_URL|g" /usr/local/etc/raddb/mods-available/privacyidea
fi

if [ -n "$PRIVACYIDEA_VALIDATE_SSL" ]; then
    log "Setting PrivacyIDEA SSL validation: $PRIVACYIDEA_VALIDATE_SSL"
    sed -i "s|VALIDATE_SSL|$PRIVACYIDEA_VALIDATE_SSL|g" /usr/local/share/freeradius/privacyidea_auth.py
fi

# Enable required modules
cd /usr/local/etc/raddb/mods-enabled
ln -sf ../mods-available/privacyidea privacyidea 2>/dev/null || true
ln -sf ../mods-available/python3 python3 2>/dev/null || true
ln -sf ../mods-available/rest rest 2>/dev/null || true

# Enable sites
cd /usr/local/etc/raddb/sites-enabled
ln -sf ../sites-available/privacyidea privacyidea 2>/dev/null || true
ln -sf ../sites-available/proxy proxy 2>/dev/null || true

# Test configuration
log "Testing FreeRADIUS configuration..."
radiusd -C -d /usr/local/etc/raddb

log "Starting FreeRADIUS..."
exec "$@"