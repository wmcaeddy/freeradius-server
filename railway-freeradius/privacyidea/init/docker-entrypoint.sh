#!/bin/bash
set -e

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

# Check if running as root
if [ "$(id -u)" = "0" ]; then
    log "Running as root, setting up permissions..."
    
    # Create directories if they don't exist
    mkdir -p /app/data/privacyidea /var/log/privacyidea /var/run/privacyidea
    
    # Set permissions
    chown -R privacyidea:privacyidea /app/data/privacyidea /var/log/privacyidea /var/run/privacyidea /opt/privacyidea
    
    # Generate SSL certificates if they don't exist
    if [ ! -f "/etc/nginx/ssl/cert.pem" ]; then
        log "Generating SSL certificates..."
        mkdir -p /etc/nginx/ssl
        cd /etc/nginx/ssl
        
        # Generate self-signed certificate
        openssl req -new -x509 -keyout key.pem -out cert.pem -days 365 -nodes \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=privacyidea.local"
        
        chmod 600 key.pem
        chmod 644 cert.pem
        chown privacyidea:privacyidea key.pem cert.pem
        cd -
    fi
    
    # Start Redis server
    redis-server --daemonize yes --port 6379
    
    # Execute the original command as privacyidea user
    exec gosu privacyidea "$0" "$@"
fi

# From here we're running as privacyidea user
log "Starting PrivacyIDEA initialization..."

# Set environment variables
export PRIVACYIDEA_CONFIGFILE=/etc/privacyidea/pi.cfg
export FLASK_APP=privacyidea.app

# Initialize database if it doesn't exist
if [ ! -f "/app/data/privacyidea/privacyidea.db" ]; then
    log "Initializing PrivacyIDEA database..."
    /usr/local/bin/init-privacyidea.sh
fi

# Update configuration with environment variables
log "Updating configuration with environment variables..."

# Update secret key
if [ -n "$PI_SECRET_KEY" ]; then
    sed -i "s/SECRET_KEY = 'your-secret-key-here'/SECRET_KEY = '$PI_SECRET_KEY'/" /etc/privacyidea/pi.cfg
fi

# Update pepper
if [ -n "$PI_PEPPER" ]; then
    sed -i "s/PI_PEPPER = 'your-pepper-here'/PI_PEPPER = '$PI_PEPPER'/" /etc/privacyidea/pi.cfg
fi

# Update database URL if using PostgreSQL or MySQL
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

log "PrivacyIDEA initialization complete"
log "Starting services..."

# Execute the command (supervisor)
exec "$@"