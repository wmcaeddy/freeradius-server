#!/bin/bash
set -e

# Persistent data directory
mkdir -p /app/data/freeradius/logs /app/data/freeradius/config /app/data/freeradius/certs /app/data/mysql

# If no external MYSQL_HOST is specified, start embedded local MariaDB server
if [ -z "$MYSQL_HOST" ] || [ "$MYSQL_HOST" = "localhost" ] || [ "$MYSQL_HOST" = "127.0.0.1" ]; then
    echo "Initializing local MariaDB server..."
    if [ ! -d "/var/lib/mysql/mysql" ]; then
        mysql_install_db --user=mysql --datadir=/var/lib/mysql
    fi
    service mariadb start || service mysql start

    # Initialize daloRADIUS database schema & user if not exists
    mysql -e "CREATE DATABASE IF NOT EXISTS radius;" || true
    mysql -e "CREATE USER IF NOT EXISTS 'radius'@'localhost' IDENTIFIED BY 'radius';" || true
    mysql -e "CREATE USER IF NOT EXISTS 'radius'@'127.0.0.1' IDENTIFIED BY 'radius';" || true
    mysql -e "GRANT ALL PRIVILEGES ON radius.* TO 'radius'@'localhost';" || true
    mysql -e "GRANT ALL PRIVILEGES ON radius.* TO 'radius'@'127.0.0.1';" || true
    mysql -e "FLUSH PRIVILEGES;" || true

    # Import FreeRADIUS base schema
    FR_SCHEMA=$(find /etc/freeradius/3.0 -path "*/mysql/schema.sql" | head -n 1)
    if [ -z "$FR_SCHEMA" ]; then
        FR_SCHEMA=$(find /etc/freeradius -path "*/mysql/schema.sql" | head -n 1)
    fi
    if [ -n "$FR_SCHEMA" ]; then
        echo "Importing FreeRADIUS schema from $FR_SCHEMA..."
        mysql radius < "$FR_SCHEMA" || true
    fi

    # Import daloRADIUS tables
    for SQL_FILE in $(find /var/www/html/daloradius/contrib/db -name "*.sql" | sort); do
        echo "Importing daloRADIUS schema from $SQL_FILE..."
        mysql radius < "$SQL_FILE" || true
    done
fi

# Enable PHP display_errors and log errors
PHP_INI=$(php -i | grep "Loaded Configuration File" | awk '{print $NF}')
if [ -f "$PHP_INI" ]; then
    sed -i "s/display_errors = .*/display_errors = On/" "$PHP_INI"
    sed -i "s/display_startup_errors = .*/display_startup_errors = On/" "$PHP_INI"
fi

# Configure all daloRADIUS config files with DB type 'mysqli'
for DALO_CONF in $(find /var/www/html/daloradius -name "daloradius.conf.php"); do
    sed -i "s/\$configValues\['CONFIG_DB_ENGINE'\] = .*/\$configValues\['CONFIG_DB_ENGINE'\] = 'mysqli';/" "$DALO_CONF"
    sed -i "s/\$configValues\['CONFIG_DB_HOST'\] = .*/\$configValues\['CONFIG_DB_HOST'\] = '127.0.0.1';/" "$DALO_CONF"
    sed -i "s/\$configValues\['CONFIG_DB_PORT'\] = .*/\$configValues\['CONFIG_DB_PORT'\] = '${MYSQL_PORT:-3306}';/" "$DALO_CONF"
    sed -i "s/\$configValues\['CONFIG_DB_USER'\] = .*/\$configValues\['CONFIG_DB_USER'\] = '${MYSQL_USER:-radius}';/" "$DALO_CONF"
    sed -i "s/\$configValues\['CONFIG_DB_PASS'\] = .*/\$configValues\['CONFIG_DB_PASS'\] = '${MYSQL_PASSWORD:-radius}';/" "$DALO_CONF"
    sed -i "s/\$configValues\['CONFIG_DB_NAME'\] = .*/\$configValues\['CONFIG_DB_NAME'\] = '${MYSQL_DATABASE:-radius}';/" "$DALO_CONF"
done

echo "Starting Apache for daloRADIUS Web Admin UI..."
apache2ctl start

echo "Starting FreeRADIUS service..."
exec freeradius -f -l stdout
