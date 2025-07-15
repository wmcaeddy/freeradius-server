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

# Create default resolver
log "Creating default resolver..."
pi-manage resolver create -n "local" -t "passwdresolver" -i "filename=/etc/passwd"

# Create default realm
log "Creating default realm..."
pi-manage realm create -n "default" -r "local" --default

# Configure default settings
log "Configuring default settings..."
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

# Create default policies
log "Creating default policies..."
pi-manage policy create -n "auth_policy" -s "authentication" -a "otppin=tokenpin"
pi-manage policy create -n "authz_policy" -s "authorization" -a "tokentype=hotp totp vasco"
pi-manage policy create -n "webui_policy" -s "webui" -a "loginmode=userstore"

log "PrivacyIDEA initialization completed successfully!"
log "Default admin credentials: admin / $ADMIN_PASSWORD"
log "Web interface will be available at the service URL"