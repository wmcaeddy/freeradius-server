#!/bin/bash
set -e

# Persistent data directory
mkdir -p /app/data/freeradius/logs /app/data/freeradius/config /app/data/freeradius/certs

# Enable PHP display_errors and log errors to stdout/stderr
PHP_INI=$(php -i | grep "Loaded Configuration File" | awk '{print $NF}')
if [ -f "$PHP_INI" ]; then
    sed -i "s/display_errors = .*/display_errors = On/" "$PHP_INI"
    sed -i "s/display_startup_errors = .*/display_startup_errors = On/" "$PHP_INI"
    sed -i "s/error_reporting = .*/error_reporting = E_ALL \& ~E_DEPRECATED \& ~E_STRICT/" "$PHP_INI"
fi

# Find and configure all daloRADIUS configuration files
for DALO_CONF in $(find /var/www/html/daloradius -name "daloradius.conf.php"); do
    sed -i "s/\$configValues\['CONFIG_DB_HOST'\] = .*/\$configValues\['CONFIG_DB_HOST'\] = '${MYSQL_HOST:-localhost}';/" "$DALO_CONF"
    sed -i "s/\$configValues\['CONFIG_DB_PORT'\] = .*/\$configValues\['CONFIG_DB_PORT'\] = '${MYSQL_PORT:-3306}';/" "$DALO_CONF"
    sed -i "s/\$configValues\['CONFIG_DB_USER'\] = .*/\$configValues\['CONFIG_DB_USER'\] = '${MYSQL_USER:-radius}';/" "$DALO_CONF"
    sed -i "s/\$configValues\['CONFIG_DB_PASS'\] = .*/\$configValues\['CONFIG_DB_PASS'\] = '${MYSQL_PASSWORD:-radius}';/" "$DALO_CONF"
    sed -i "s/\$configValues\['CONFIG_DB_NAME'\] = .*/\$configValues\['CONFIG_DB_NAME'\] = '${MYSQL_DATABASE:-radius}';/" "$DALO_CONF"
done

echo "Starting Apache for daloRADIUS Web Admin UI..."
apache2ctl start

echo "Starting FreeRADIUS service..."
exec freeradius -f -l stdout
