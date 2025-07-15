# PrivacyIDEA Server for Railway.com deployment
FROM ubuntu:22.04

# Build arguments
ARG PRIVACYIDEA_VERSION=3.9.2

# Install system dependencies
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    python3-venv \
    libssl-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    zlib1g-dev \
    libldap2-dev \
    libsasl2-dev \
    libmysqlclient-dev \
    libpq-dev \
    libsqlite3-dev \
    redis-server \
    nginx \
    supervisor \
    wget \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Create privacyidea user
RUN groupadd -r privacyidea && \
    useradd -r -g privacyidea -d /opt/privacyidea -s /bin/bash privacyidea

# Create directories
RUN mkdir -p /opt/privacyidea /var/log/privacyidea /etc/privacyidea /app/data/privacyidea

# Install PrivacyIDEA
RUN pip3 install --upgrade pip setuptools wheel && \
    pip3 install privacyidea==${PRIVACYIDEA_VERSION} && \
    pip3 install gunicorn redis psycopg2-binary mysqlclient

# Copy configuration files
COPY railway-freeradius/privacyidea/config/pi.cfg /etc/privacyidea/pi.cfg
COPY railway-freeradius/privacyidea/config/gunicorn.conf.py /etc/privacyidea/gunicorn.conf.py
COPY railway-freeradius/privacyidea/nginx/privacyidea.conf /etc/nginx/sites-available/privacyidea
COPY railway-freeradius/privacyidea/init/init-privacyidea.sh /usr/local/bin/init-privacyidea.sh
COPY railway-freeradius/privacyidea/init/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Configure nginx
RUN rm -f /etc/nginx/sites-enabled/default && \
    ln -s /etc/nginx/sites-available/privacyidea /etc/nginx/sites-enabled/privacyidea

# Set permissions
RUN chown -R privacyidea:privacyidea /opt/privacyidea /var/log/privacyidea /etc/privacyidea /app/data/privacyidea && \
    chmod +x /usr/local/bin/init-privacyidea.sh

# Create SSL certificates directory
RUN mkdir -p /etc/nginx/ssl && chown -R privacyidea:privacyidea /etc/nginx/ssl

# Expose ports
EXPOSE 80 443

# Volume for persistent data
VOLUME ["/app/data"]

# Set working directory
WORKDIR /opt/privacyidea

# Entry point script
COPY railway-freeradius/privacyidea/init/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Start supervisor
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]