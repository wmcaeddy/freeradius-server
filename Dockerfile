# Use pre-built FreeRADIUS from packages instead of building from source
FROM ubuntu:22.04

# Set environment variables to avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Install all dependencies in one go to reduce layers
RUN apt-get update && apt-get install -y --no-install-recommends \
    freeradius \
    freeradius-python3 \
    freeradius-rest \
    python3 \
    python3-pip \
    python3-requests \
    python3-flask \
    python3-flask-sqlalchemy \
    python3-passlib \
    nginx \
    supervisor \
    redis-server \
    libssl3 \
    libsqlite3-0 \
    curl \
    ca-certificates \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Install only essential Python packages via pip
RUN pip3 install --no-cache-dir \
    pyrad \
    gunicorn

# Create users (freerad user already exists from package)
RUN groupadd -r privacyidea && \
    useradd -r -g privacyidea -d /opt/privacyidea -s /bin/bash privacyidea

# Create required directories
RUN mkdir -p /app/data /var/log/privacyidea /etc/privacyidea /opt/privacyidea && \
    chown -R freerad:freerad /app/data && \
    chown -R privacyidea:privacyidea /var/log/privacyidea /etc/privacyidea /opt/privacyidea

# Copy configuration files
COPY railway-freeradius/config/radiusd.conf /etc/freeradius/3.0/radiusd.conf
COPY railway-freeradius/config/mods-available/* /etc/freeradius/3.0/mods-available/
COPY railway-freeradius/config/sites-available/* /etc/freeradius/3.0/sites-available/
COPY railway-freeradius/scripts/simple_token_auth.py /usr/share/freeradius/
COPY railway-freeradius/scripts/proxy_loadbalance.py /usr/share/freeradius/
COPY railway-freeradius/scripts/setup-demo-tokens.py /usr/local/bin/
COPY railway-freeradius/scripts/docker-entrypoint.sh /docker-entrypoint.sh

# Create simple nginx config for status page
RUN echo 'server { listen 80; location / { return 200 "FreeRADIUS is running\n"; add_header Content-Type text/plain; } }' > /etc/nginx/sites-available/default

# Set permissions
RUN chown -R freerad:freerad /etc/freeradius && \
    chmod +x /docker-entrypoint.sh /usr/local/bin/setup-demo-tokens.py

# Create startup script for Railway
COPY railway-freeradius/scripts/railway-start.sh /railway-start.sh
RUN chmod +x /railway-start.sh

# Expose ports
EXPOSE 80 443 1812/udp 1813/udp 18120/tcp 11812/udp 11813/udp

# Set working directory
WORKDIR /etc/freeradius/3.0

# Entry point
ENTRYPOINT ["/railway-start.sh"]