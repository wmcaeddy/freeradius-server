FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Install FreeRADIUS, PHP 7.4, Apache, MariaDB, git, and required extensions for daloRADIUS
RUN apt-get update && apt-get install -y --no-install-recommends \
    freeradius \
    freeradius-mysql \
    freeradius-utils \
    mariadb-server \
    apache2 \
    php \
    php-mysql \
    php-gd \
    php-curl \
    php-mbstring \
    php-xml \
    php-zip \
    php-pear \
    php-db \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install MDB2 and MDB2_Driver_mysqli
RUN pear install MDB2 MDB2_Driver_mysqli || true

# Clone daloRADIUS master branch into web root
RUN git clone --depth 1 https://github.com/lirantal/daloradius.git /var/www/html/daloradius && \
    ( [ -f /var/www/html/daloradius/app/common/includes/daloradius.conf.php.template ] && cp /var/www/html/daloradius/app/common/includes/daloradius.conf.php.template /var/www/html/daloradius/app/common/includes/daloradius.conf.php || true ) && \
    ( [ -f /var/www/html/daloradius/library/daloradius.conf.php.template ] && cp /var/www/html/daloradius/library/daloradius.conf.php.template /var/www/html/daloradius/library/daloradius.conf.php || true ) && \
    chown -R www-data:www-data /var/www/html/daloradius && \
    chmod -R 755 /var/www/html/daloradius

# Create Apache config pointing DirectoryIndex directly to daloRADIUS login
RUN echo 'ServerName localhost\n<Directory /var/www/html>\n Options Indexes FollowSymLinks\n AllowOverride All\n Require all granted\n</Directory>\n<Directory /var/www/html/daloradius>\n DirectoryIndex app/users/login.php login.php index.php\n Options Indexes FollowSymLinks\n AllowOverride All\n Require all granted\n</Directory>' > /etc/apache2/conf-available/daloradius.conf && \
    a2enconf daloradius

# Redirect root daloradius request directly to login page
RUN echo '<?php header("Location: /daloradius/app/users/login.php"); exit; ?>' > /var/www/html/daloradius/index.php
RUN echo '<?php header("Location: /daloradius/app/users/login.php"); exit; ?>' > /var/www/html/index.php

# Create data directories
RUN mkdir -p /app/data /etc/freeradius/3.0 && \
    chown -R freerad:freerad /app/data

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 80 1812/udp 1813/udp

WORKDIR /var/www/html/daloradius

ENTRYPOINT ["/docker-entrypoint.sh"]
