FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Install FreeRADIUS, PHP, Apache, git, and required extensions for daloRADIUS
RUN apt-get update && apt-get install -y --no-install-recommends \
    freeradius \
    freeradius-mysql \
    freeradius-utils \
    apache2 \
    php \
    php-mysql \
    php-gd \
    php-curl \
    php-mbstring \
    php-xml \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Clone daloRADIUS into web root
RUN git clone --depth 1 https://github.com/lirantal/daloradius.git /var/www/html/daloradius && \
    ( [ -f /var/www/html/daloradius/app/common/includes/daloradius.conf.php.template ] && cp /var/www/html/daloradius/app/common/includes/daloradius.conf.php.template /var/www/html/daloradius/app/common/includes/daloradius.conf.php || true ) && \
    ( [ -f /var/www/html/daloradius/library/daloradius.conf.php.template ] && cp /var/www/html/daloradius/library/daloradius.conf.php.template /var/www/html/daloradius/library/daloradius.conf.php || true ) && \
    chown -R www-data:www-data /var/www/html/daloradius && \
    chmod -R 755 /var/www/html/daloradius

# Create Apache config with DirectoryIndex and global permissions
RUN echo 'ServerName localhost\n<Directory /var/www/html>\n Options Indexes FollowSymLinks\n AllowOverride All\n Require all granted\n</Directory>\n<Directory /var/www/html/daloradius>\n DirectoryIndex index.php login.php\n Options Indexes FollowSymLinks\n AllowOverride All\n Require all granted\n</Directory>' > /etc/apache2/conf-available/daloradius.conf && \
    a2enconf daloradius

# Set Apache default document root redirect to /daloradius
RUN echo '<?php header("Location: /daloradius/login.php"); exit; ?>' > /var/www/html/index.php

# Create data directories
RUN mkdir -p /app/data /etc/freeradius/3.0 && \
    chown -R freerad:freerad /app/data

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 80 1812/udp 1813/udp

WORKDIR /var/www/html/daloradius

ENTRYPOINT ["/docker-entrypoint.sh"]
