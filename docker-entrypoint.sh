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

    # Import FreeRADIUS base schema for MySQL
    FR_SCHEMA=$(find /etc/freeradius/3.0 -path "*/mysql/schema.sql" | head -n 1)
    if [ -z "$FR_SCHEMA" ]; then
        FR_SCHEMA=$(find /etc/freeradius -path "*/mysql/schema.sql" | head -n 1)
    fi
    if [ -n "$FR_SCHEMA" ]; then
        echo "Importing FreeRADIUS schema from $FR_SCHEMA..."
        mysql radius < "$FR_SCHEMA" || true
    fi

    # Import canonical daloRADIUS tables only (exclude migration files)
    for SQL_FILE in $(find /var/www/html/daloradius/contrib/db -maxdepth 1 -type f \( -name "*mariadb*.sql" -o -name "*mysql*.sql" \) ! -name "*pgsql*" ! -name "*migrate*" | sort); do
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

# Write full daloRADIUS config with DB_ENGINE = pdo
for DALO_CONF in $(find /var/www/html/daloradius -name "daloradius.conf.php"); do
    cat << 'CONF' > "$DALO_CONF"
<?php
$configValues['CONFIG_DB_ENGINE'] = 'pdo';
$configValues['CONFIG_DB_TYPE'] = 'mysql';
$configValues['CONFIG_DB_HOST'] = '127.0.0.1';
$configValues['CONFIG_DB_PORT'] = '3306';
$configValues['CONFIG_DB_USER'] = 'radius';
$configValues['CONFIG_DB_PASS'] = 'radius';
$configValues['CONFIG_DB_NAME'] = 'radius';
$configValues['DB_TYPE'] = 'mysql';
$configValues['DB_HOST'] = '127.0.0.1';
$configValues['DB_PORT'] = '3306';
$configValues['DB_USER'] = 'radius';
$configValues['DB_PASS'] = 'radius';
$configValues['DB_NAME'] = 'radius';
$configValues['CONFIG_FILE_DALORADIUS_VERSION'] = '1.3';
$configValues['CONFIG_MAINT_TEST_USER'] = 'administrator';
CONF
done

echo "Starting Apache for daloRADIUS Web Admin UI..."
apache2ctl start

echo "Starting FreeRADIUS service..."
exec freeradius -f -l stdout
