#!/bin/bash
# Initialize PrivacyIDEA database and configuration

set -e

export PRIVACYIDEA_CONFIGFILE=/etc/privacyidea/pi.cfg
export FLASK_APP=privacyidea.app

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] INIT: $*"
}

log "Starting PrivacyIDEA initialization..."

# Create database tables
log "Creating database tables..."
pi-manage createdb

# Generate encryption key
log "Generating encryption key..."
if [ ! -f "/app/data/privacyidea/enckey" ]; then
    pi-manage create_enckey
fi

# Generate audit keys
log "Generating audit keys..."
if [ ! -f "/app/data/privacyidea/private.pem" ]; then
    pi-manage create_audit_keys
fi

# Create admin user
log "Creating admin user..."
ADMIN_PASSWORD=${PI_ADMIN_PASSWORD:-admin}
pi-manage admin add admin -e admin@localhost -p "$ADMIN_PASSWORD"

# Create default policies
log "Creating default policies..."

# Authentication policy
pi-manage policy create -n "auth_policy" -s "authentication" -a "otppin=tokenpin" -r "admin"

# Authorization policy  
pi-manage policy create -n "authz_policy" -s "authorization" -a "tokentype=hotp totp" -r "admin"

# Web UI policy
pi-manage policy create -n "webui_policy" -s "webui" -a "loginmode=userstore" -r "admin"

# Create default resolver
log "Creating default resolver..."
pi-manage resolver create -n "local" -t "passwdresolver" -i "filename=/etc/passwd"

# Create default realm
log "Creating default realm..."
pi-manage realm create -n "default" -r "local" --default

# Create demo tokens for testing
log "Creating demo tokens..."

# Create demo user
pi-manage user create -r "default" -u "demo" -g "Demo" -s "User" -e "demo@localhost"

# Create HOTP token for demo user
pi-manage token create -t "hotp" -u "demo" -r "default" -s "3132333435363738393031323334353637383930"

# Create TOTP token for demo user
pi-manage token create -t "totp" -u "demo" -r "default" -s "3132333435363738393031323334353637383930"

# Create Vasco demo token if configured
if [ "$VASCO_ENABLED" = "true" ]; then
    log "Creating Vasco demo token..."
    pi-manage token create -t "vasco" -u "vasco_demo" -r "default" -s "vasco_demo_secret"
fi

# Set up RADIUS configuration
log "Setting up RADIUS configuration..."
pi-manage config set -k "radius.enabled" -v "True"
pi-manage config set -k "radius.timeout" -v "10"
pi-manage config set -k "radius.retries" -v "3"

# Enable token types
pi-manage config set -k "tokens.hotp.enabled" -v "True"
pi-manage config set -k "tokens.totp.enabled" -v "True"
pi-manage config set -k "tokens.vasco.enabled" -v "True"

# Configure default token settings
pi-manage config set -k "default.tokentype" -v "hotp"
pi-manage config set -k "default.otplen" -v "6"
pi-manage config set -k "default.timewindow" -v "300"

# Configure authentication
pi-manage config set -k "auth.cache.timeout" -v "3600"
pi-manage config set -k "auth.passthrough" -v "False"

# Configure enrollment
pi-manage config set -k "enrollment.enabled" -v "True"

log "PrivacyIDEA initialization completed successfully!"
log "Default admin credentials: admin / $ADMIN_PASSWORD"
log "Demo user credentials: demo (use with token)"
log "Vasco demo user: vasco_demo (use with Vasco token)"