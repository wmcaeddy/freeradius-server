# Multi-stage build for FreeRADIUS with PrivacyIDEA support
FROM ubuntu:22.04 AS builder

# Build arguments
ARG FREERADIUS_VERSION=3.2.3
ARG PRIVACYIDEA_VERSION=3.8

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    wget \
    libssl-dev \
    libtalloc-dev \
    libkqueue-dev \
    libcap-dev \
    libpcre3-dev \
    libyajl-dev \
    libcurl4-openssl-dev \
    libpam0g-dev \
    libreadline-dev \
    libsqlite3-dev \
    libperl-dev \
    python3-dev \
    python3-pip \
    autoconf \
    libtool \
    && rm -rf /var/lib/apt/lists/*

# Build FreeRADIUS from source
WORKDIR /tmp
RUN wget https://github.com/FreeRADIUS/freeradius-server/releases/download/release_${FREERADIUS_VERSION//./_}/freeradius-server-${FREERADIUS_VERSION}.tar.gz \
    && tar -xzf freeradius-server-${FREERADIUS_VERSION}.tar.gz \
    && cd freeradius-server-${FREERADIUS_VERSION} \
    && ./configure --prefix=/usr/local \
        --with-rlm_python3 \
        --with-rlm_rest \
        --with-rlm_pap \
        --with-rlm_chap \
        --with-rlm_mschap \
    && make -j$(nproc) \
    && make install

# Install Python dependencies for PrivacyIDEA
RUN pip3 install --no-cache-dir \
    privacyidea \
    requests \
    pyrad

# Runtime stage
FROM ubuntu:22.04

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libssl3 \
    libtalloc2 \
    libpcre3 \
    libyajl2 \
    libcurl4 \
    libpam0g \
    libreadline8 \
    libsqlite3-0 \
    libperl5.34 \
    python3 \
    python3-pip \
    ca-certificates \
    curl \
    redis-server \
    nginx \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Copy FreeRADIUS from builder
COPY --from=builder /usr/local /usr/local

# Install Python runtime dependencies
RUN pip3 install --no-cache-dir \
    privacyidea \
    requests \
    pyrad \
    gunicorn

# Create users
RUN groupadd -r -g 101 freerad && \
    useradd -r -g freerad -u 101 -d /etc/raddb -s /usr/sbin/nologin freerad && \
    groupadd -r privacyidea && \
    useradd -r -g privacyidea -d /opt/privacyidea -s /bin/bash privacyidea

# Create required directories
RUN mkdir -p /app/data /var/log/radius /var/run/radiusd /var/log/privacyidea /etc/privacyidea /opt/privacyidea && \
    chown -R freerad:freerad /app/data /var/log/radius /var/run/radiusd && \
    chown -R privacyidea:privacyidea /var/log/privacyidea /etc/privacyidea /opt/privacyidea

# Copy configuration files
COPY railway-freeradius/config/radiusd.conf /usr/local/etc/raddb/radiusd.conf
COPY railway-freeradius/config/mods-available/* /usr/local/etc/raddb/mods-available/
COPY railway-freeradius/config/sites-available/* /usr/local/etc/raddb/sites-available/
COPY railway-freeradius/scripts/privacyidea_auth.py /usr/local/share/freeradius/
COPY railway-freeradius/scripts/proxy_loadbalance.py /usr/local/share/freeradius/
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
RUN chown -R freerad:freerad /usr/local/etc/raddb && \
    chmod +x /docker-entrypoint.sh /usr/local/bin/init-privacyidea.sh /usr/local/bin/privacyidea-entrypoint.sh /usr/local/bin/setup-demo-tokens.py

# Create startup script for Railway
COPY railway-freeradius/scripts/railway-start.sh /railway-start.sh
RUN chmod +x /railway-start.sh

# Expose ports
EXPOSE 80 443 1812/udp 1813/udp 18120/tcp 11812/udp 11813/udp

# Volume for persistent data
VOLUME ["/app/data"]

# Set working directory
WORKDIR /usr/local/etc/raddb

# Entry point
ENTRYPOINT ["/railway-start.sh"]