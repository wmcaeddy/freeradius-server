# PrivacyIDEA Service - Standalone deployment for Railway.com
FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
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
    curl \
    ca-certificates \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Create privacyidea user
RUN groupadd -r privacyidea && \
    useradd -r -g privacyidea -d /opt/privacyidea -s /bin/bash privacyidea

# Create required directories
RUN mkdir -p /app/data/privacyidea /var/log/privacyidea /etc/privacyidea /opt/privacyidea && \
    chown -R privacyidea:privacyidea /app/data /var/log/privacyidea /etc/privacyidea /opt/privacyidea

# Install PrivacyIDEA and dependencies
RUN pip3 install --no-cache-dir \
    privacyidea==3.9.2 \
    gunicorn \
    redis \
    psycopg2-binary \
    mysqlclient \
    requests

# Copy configuration files
COPY config/pi.cfg /etc/privacyidea/pi.cfg
COPY config/gunicorn.conf.py /etc/privacyidea/gunicorn.conf.py
COPY nginx/privacyidea.conf /etc/nginx/sites-available/privacyidea
COPY scripts/init-privacyidea.sh /usr/local/bin/init-privacyidea.sh
COPY scripts/setup-demo-tokens.py /usr/local/bin/setup-demo-tokens.py
COPY scripts/docker-entrypoint.sh /docker-entrypoint.sh

# Configure nginx
RUN rm -f /etc/nginx/sites-enabled/default && \
    ln -s /etc/nginx/sites-available/privacyidea /etc/nginx/sites-enabled/privacyidea

# Set permissions
RUN chown -R privacyidea:privacyidea /etc/privacyidea && \
    chmod +x /docker-entrypoint.sh /usr/local/bin/init-privacyidea.sh /usr/local/bin/setup-demo-tokens.py

# Expose ports
EXPOSE 80 443

# Set working directory
WORKDIR /opt/privacyidea

# Entry point
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]