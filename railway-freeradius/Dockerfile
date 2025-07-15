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
    && rm -rf /var/lib/apt/lists/*

# Copy FreeRADIUS from builder
COPY --from=builder /usr/local /usr/local

# Install Python runtime dependencies
RUN pip3 install --no-cache-dir \
    privacyidea \
    requests \
    pyrad

# Create FreeRADIUS user
RUN groupadd -r -g 101 freerad && \
    useradd -r -g freerad -u 101 -d /etc/raddb -s /usr/sbin/nologin freerad

# Create required directories
RUN mkdir -p /app/data /var/log/radius /var/run/radiusd && \
    chown -R freerad:freerad /app/data /var/log/radius /var/run/radiusd

# Copy configuration files
COPY config/radiusd.conf /usr/local/etc/raddb/radiusd.conf
COPY config/mods-available/* /usr/local/etc/raddb/mods-available/
COPY config/sites-available/* /usr/local/etc/raddb/sites-available/
COPY scripts/privacyidea_auth.py /usr/local/share/freeradius/
COPY scripts/docker-entrypoint.sh /docker-entrypoint.sh

# Set permissions
RUN chown -R freerad:freerad /usr/local/etc/raddb && \
    chmod +x /docker-entrypoint.sh

# Expose RADIUS ports
EXPOSE 1812/udp 1813/udp 18120/tcp

# Volume for persistent data
VOLUME ["/app/data"]

# Set working directory
WORKDIR /usr/local/etc/raddb

# Switch to non-root user
USER freerad

# Entry point
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["radiusd", "-f", "-d", "/usr/local/etc/raddb"]