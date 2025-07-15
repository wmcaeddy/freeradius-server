#!/bin/bash
# PrivacyIDEA Service Entry Point for Railway.com

set -e

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] PRIVACYIDEA: $*"
}

log "Starting PrivacyIDEA service..."

# Ensure data directory exists
mkdir -p /app/data/privacyidea

# Set permissions
chown -R privacyidea:privacyidea /app/data /var/log/privacyidea /opt/privacyidea

# Start Redis
log "Starting Redis server..."
redis-server --daemonize yes --port 6379

# Update configuration with environment variables
log "Updating configuration with environment variables..."
if [ -n "$PI_SECRET_KEY" ]; then
    sed -i "s/SECRET_KEY = 'your-secret-key-here'/SECRET_KEY = '$PI_SECRET_KEY'/" /etc/privacyidea/pi.cfg
fi

if [ -n "$PI_PEPPER" ]; then
    sed -i "s/PI_PEPPER = 'your-pepper-here'/PI_PEPPER = '$PI_PEPPER'/" /etc/privacyidea/pi.cfg
fi

# Update database URL if using external database
if [ -n "$DATABASE_URL" ]; then
    sed -i "s|SQLALCHEMY_DATABASE_URI = 'sqlite:////app/data/privacyidea/privacyidea.db'|SQLALCHEMY_DATABASE_URI = '$DATABASE_URL'|" /etc/privacyidea/pi.cfg
fi

# Update Redis configuration
if [ -n "$REDIS_URL" ]; then
    # Parse Redis URL and update configuration
    REDIS_HOST=$(echo $REDIS_URL | cut -d'@' -f2 | cut -d':' -f1)
    REDIS_PORT=$(echo $REDIS_URL | cut -d':' -f3)
    
    if [ -n "$REDIS_HOST" ] && [ -n "$REDIS_PORT" ]; then
        sed -i "s/CACHE_REDIS_HOST = 'localhost'/CACHE_REDIS_HOST = '$REDIS_HOST'/" /etc/privacyidea/pi.cfg
        sed -i "s/CACHE_REDIS_PORT = 6379/CACHE_REDIS_PORT = $REDIS_PORT/" /etc/privacyidea/pi.cfg
    fi
fi

# Initialize PrivacyIDEA database if needed
export PRIVACYIDEA_CONFIGFILE=/etc/privacyidea/pi.cfg
export FLASK_APP=privacyidea.app

if [ ! -f "/app/data/privacyidea/privacyidea.db" ]; then
    log "Initializing PrivacyIDEA database..."
    runuser -u privacyidea -- /usr/local/bin/init-privacyidea.sh
    
    # Set up demo tokens
    log "Setting up demo tokens..."
    runuser -u privacyidea -- python3 /usr/local/bin/setup-demo-tokens.py
fi

# Start PrivacyIDEA
log "Starting PrivacyIDEA application server..."
runuser -u privacyidea -- gunicorn --config /etc/privacyidea/gunicorn.conf.py privacyidea.app:application &

# Start Nginx
log "Starting Nginx reverse proxy..."
nginx -g "daemon off;" &

# Wait for services to start
sleep 5

# Health check
log "Performing health check..."
if curl -f http://localhost/health > /dev/null 2>&1; then
    log "PrivacyIDEA service is healthy and ready"
else
    log "Warning: Health check failed, but continuing..."
fi

# Keep the container running
log "PrivacyIDEA service startup complete"
wait