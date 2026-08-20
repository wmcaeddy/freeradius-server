#!/bin/bash
set -e

# Persistent data directory
mkdir -p /app/data/freeradius/logs /app/data/freeradius/config /app/data/freeradius/certs

# Find and configure daloRADIUS database connection
DALO_CONF=$(find /var/www/html/daloradius -name "daloradius.conf.php" | head -n 1)
if [ -n "$DALO_CONF" ] && [ -f "$DALO_CONF" ]; then
    sed -i "s/\$configValues\['CONFIG_DB_HOST'\] = .*/\$configValues\['CONFIG_DB_HOST'\] = '${MYSQL_HOST:-localhost}';/" "$DALO_CONF"
    sed -i "s/\$configValues\['CONFIG_DB_PORT'\] = .*/\$configValues\['CONFIG_DB_PORT'\] = '${MYSQL_PORT:-3306}';/" "$DALO_CONF"
    sed -i "s/\$configValues\['CONFIG_DB_USER'\] = .*/\$configValues\['CONFIG_DB_USER'\] = '${MYSQL_USER:-radius}';/" "$DALO_CONF"
    sed -i "s/\$configValues\['CONFIG_DB_PASS'\] = .*/\$configValues\['CONFIG_DB_PASS'\] = '${MYSQL_PASSWORD:-radius}';/" "$DALO_CONF"
    sed -i "s/\$configValues\['CONFIG_DB_NAME'\] = .*/\$configValues\['CONFIG_DB_NAME'\] = '${MYSQL_DATABASE:-radius}';/" "$DALO_CONF"
fi

echo "Starting Apache for daloRADIUS Web Admin UI..."
service apache2 start || apache2ctl start

echo "Starting FreeRADIUS service..."
exec freeradius -f -l stdout
