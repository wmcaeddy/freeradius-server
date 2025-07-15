#!/bin/bash
# Railway.com startup script for FreeRADIUS + PrivacyIDEA

set -e

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

log "Starting Railway.com FreeRADIUS + PrivacyIDEA deployment..."

# Ensure data directory exists
mkdir -p /app/data/privacyidea

# Start Redis
log "Starting Redis server..."
redis-server --daemonize yes --port 6379

# Initialize PrivacyIDEA if needed
export PRIVACYIDEA_CONFIGFILE=/etc/privacyidea/pi.cfg
export FLASK_APP=privacyidea.app

# Update configuration with environment variables
log "Updating PrivacyIDEA configuration..."
if [ -n "$PI_SECRET_KEY" ]; then
    sed -i "s/SECRET_KEY = 'your-secret-key-here'/SECRET_KEY = '$PI_SECRET_KEY'/" /etc/privacyidea/pi.cfg
fi

if [ -n "$PI_PEPPER" ]; then
    sed -i "s/PI_PEPPER = 'your-pepper-here'/PI_PEPPER = '$PI_PEPPER'/" /etc/privacyidea/pi.cfg
fi

# Initialize PrivacyIDEA database
if [ ! -f "/app/data/privacyidea/privacyidea.db" ]; then
    log "Initializing PrivacyIDEA database..."
    runuser -u privacyidea -- /usr/local/bin/init-privacyidea.sh
fi

# Start PrivacyIDEA
log "Starting PrivacyIDEA server..."
runuser -u privacyidea -- gunicorn --config /etc/privacyidea/gunicorn.conf.py privacyidea.app:application &

# Start Nginx
log "Starting Nginx..."
nginx &

# Setup demo tokens
log "Setting up demo tokens..."
sleep 5  # Wait for PrivacyIDEA to be ready
python3 /usr/local/bin/setup-demo-tokens.py || log "Demo token setup failed (this is OK if already exists)"

# Configure FreeRADIUS
log "Configuring FreeRADIUS..."
chown -R freerad:freerad /etc/freeradius /app/data /var/log/freeradius /var/run/freeradius

# Enable required modules
cd /etc/freeradius/3.0/mods-enabled
ln -sf ../mods-available/privacyidea privacyidea 2>/dev/null || true
ln -sf ../mods-available/python3 python3 2>/dev/null || true

# Enable sites
cd /etc/freeradius/3.0/sites-enabled
ln -sf ../sites-available/privacyidea privacyidea 2>/dev/null || true

# Test configuration
log "Testing FreeRADIUS configuration..."
runuser -u freerad -- freeradius -C -d /etc/freeradius/3.0

# Start FreeRADIUS
log "Starting FreeRADIUS..."
exec runuser -u freerad -- freeradius -f -d /etc/freeradius/3.0