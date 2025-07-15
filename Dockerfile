# Use pre-built FreeRADIUS from packages instead of building from source
FROM ubuntu:22.04

# Set environment variables to avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Install system dependencies in smaller chunks to avoid timeouts
RUN apt-get update && apt-get install -y --no-install-recommends \
    freeradius \
    freeradius-python3 \
    freeradius-rest \
    && rm -rf /var/lib/apt/lists/*

# Install Python and basic tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install web server components
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    supervisor \
    redis-server \
    && rm -rf /var/lib/apt/lists/*

# Install additional libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    libssl3 \
    libsqlite3-0 \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python runtime dependencies
RUN pip3 install --no-cache-dir --break-system-packages \
    privacyidea \
    requests \
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
COPY railway-freeradius/scripts/privacyidea_auth.py /usr/share/freeradius/
COPY railway-freeradius/scripts/proxy_loadbalance.py /usr/share/freeradius/
COPY railway-freeradius/scripts/setup-demo-tokens.py /usr/local/bin/
COPY railway-freeradius/scripts/docker-entrypoint.sh /docker-entrypoint.sh

# Copy PrivacyIDEA configuration
COPY railway-freeradius/privacyidea/config/pi.cfg /etc/privacyidea/pi.cfg
COPY railway-freeradius/privacyidea/config/gunicorn.conf.py /etc/privacyidea/gunicorn.conf.py
COPY railway-freeradius/privacyidea/nginx/privacyidea.conf /etc/nginx/sites-available/privacyidea
COPY railway-freeradius/privacyidea/init/init-privacyidea.sh /usr/local/bin/init-privacyidea.sh
COPY railway-freeradius/privacyidea/init/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY railway-freeradius/privacyidea/init/docker-entrypoint.sh /usr/local/bin/privacyidea-entrypoint.sh

# Configure nginx
RUN rm -f /etc/nginx/sites-enabled/default && \
    ln -s /etc/nginx/sites-available/privacyidea /etc/nginx/sites-enabled/privacyidea

# Set permissions
RUN chown -R freerad:freerad /etc/freeradius && \
    chmod +x /docker-entrypoint.sh /usr/local/bin/init-privacyidea.sh /usr/local/bin/privacyidea-entrypoint.sh /usr/local/bin/setup-demo-tokens.py

# Create startup script for Railway
COPY railway-freeradius/scripts/railway-start.sh /railway-start.sh
RUN chmod +x /railway-start.sh

# Expose ports
EXPOSE 80 443 1812/udp 1813/udp 18120/tcp 11812/udp 11813/udp

# Set working directory
WORKDIR /etc/freeradius/3.0

# Entry point
ENTRYPOINT ["/railway-start.sh"]