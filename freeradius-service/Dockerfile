# FreeRADIUS Service - Standalone deployment for Railway.com
FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Install FreeRADIUS and dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    freeradius \
    freeradius-python3 \
    freeradius-rest \
    python3 \
    python3-pip \
    python3-requests \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies for PrivacyIDEA integration
RUN pip3 install --no-cache-dir \
    requests \
    pyrad

# Create required directories
RUN mkdir -p /app/data/freeradius /var/log/freeradius && \
    chown -R freerad:freerad /app/data /var/log/freeradius

# Copy configuration files
COPY config/radiusd.conf /etc/freeradius/3.0/radiusd.conf
COPY config/mods-available/* /etc/freeradius/3.0/mods-available/
COPY config/sites-available/* /etc/freeradius/3.0/sites-available/
COPY config/clients.conf /etc/freeradius/3.0/clients.conf
COPY scripts/privacyidea_client.py /usr/share/freeradius/
COPY scripts/proxy_loadbalance.py /usr/share/freeradius/
COPY scripts/docker-entrypoint.sh /docker-entrypoint.sh

# Set permissions
RUN chown -R freerad:freerad /etc/freeradius && \
    chmod +x /docker-entrypoint.sh

# Create simple status endpoint
RUN echo '#!/bin/bash\necho "FreeRADIUS is running"\n' > /usr/local/bin/status.sh && \
    chmod +x /usr/local/bin/status.sh

# Expose RADIUS ports
EXPOSE 1812/udp 1813/udp 18120/tcp

# Set working directory
WORKDIR /etc/freeradius/3.0

# Entry point
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["freeradius", "-f", "-d", "/etc/freeradius/3.0"]