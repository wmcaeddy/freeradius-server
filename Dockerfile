FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Install FreeRADIUS, PHP, Apache/Nginx, git, and required extensions for daloRADIUS
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
    cp /var/www/html/daloradius/library/daloradius.conf.php.template /var/www/html/daloradius/library/daloradius.conf.php && \
    chown -R www-data:www-data /var/www/html/daloradius

# Create data directories
RUN mkdir -p /app/data /etc/freeradius/3.0 && \
    chown -R freerad:freerad /app/data

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 80 1812/udp 1813/udp

WORKDIR /var/www/html/daloradius

ENTRYPOINT ["/docker-entrypoint.sh"]
