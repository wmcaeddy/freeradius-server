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

    # 1. Import FreeRADIUS base SQL schema
    FR_SCHEMA=$(find /etc/freeradius/3.0 -path "*/mysql/schema.sql" | head -n 1)
    if [ -z "$FR_SCHEMA" ]; then
        FR_SCHEMA=$(find /etc/freeradius -path "*/mysql/schema.sql" | head -n 1)
    fi
    if [ -n "$FR_SCHEMA" ]; then
        echo "Importing base FreeRADIUS schema from $FR_SCHEMA..."
        mysql radius < "$FR_SCHEMA" || true
    fi

    # 2. Import daloRADIUS tables
    MAIN_SCHEMA=$(find /var/www/html/daloradius/contrib/db -name "mariadb-daloradius.sql" | head -n 1)
    if [ -z "$MAIN_SCHEMA" ]; then
        MAIN_SCHEMA=$(find /var/www/html/daloradius/contrib/db -name "mysql-daloradius.sql" | head -n 1)
    fi
    DICT_SCHEMA=$(find /var/www/html/daloradius/contrib/db -name "mariadb-daloradius-dictionaries.sql" | head -n 1)
    if [ -z "$DICT_SCHEMA" ]; then
        DICT_SCHEMA=$(find /var/www/html/daloradius/contrib/db -name "mysql-daloradius-dictionaries.sql" | head -n 1)
    fi

    if [ -n "$MAIN_SCHEMA" ]; then
        echo "Importing daloRADIUS primary schema from $MAIN_SCHEMA..."
        mysql -f radius < "$MAIN_SCHEMA" || true
    fi
    if [ -n "$DICT_SCHEMA" ]; then
        echo "Importing daloRADIUS dictionary schema from $DICT_SCHEMA..."
        mysql -f radius < "$DICT_SCHEMA" || true
    fi

    # 3. Create default daloRADIUS administrator operator user
    mysql radius -e "INSERT IGNORE INTO operators (id, username, password, firstname, lastname, title, department, company, phone1, phone2, email1, email2, messenger1, messenger2, notes) VALUES (1, 'administrator', 'radius', 'Administrator', 'User', 'System Administrator', 'IT', 'Company', '', '', '', '', '', '', '');" || true
fi

# Enable PHP display_errors and log errors
PHP_INI=$(php -i | grep "Loaded Configuration File" | awk '{print $NF}')
if [ -f "$PHP_INI" ]; then
    sed -i "s/display_errors = .*/display_errors = On/" "$PHP_INI"
    sed -i "s/display_startup_errors = .*/display_startup_errors = On/" "$PHP_INI"
fi

# Configure daloRADIUS config with mysqli driver and explicit socket path
for DALO_CONF in $(find /var/www/html/daloradius -name "daloradius.conf.php"); do
    cat << 'CONF' > "$DALO_CONF"
<?php
$configValues['CONFIG_DB_ENGINE'] = 'mysqli';
$configValues['CONFIG_DB_TYPE'] = 'mysqli';
$configValues['CONFIG_DB_HOST'] = 'localhost:/var/run/mysqld/mysqld.sock';
$configValues['CONFIG_DB_PORT'] = '3306';
$configValues['CONFIG_DB_USER'] = 'radius';
$configValues['CONFIG_DB_PASS'] = 'radius';
$configValues['CONFIG_DB_NAME'] = 'radius';
$configValues['DB_TYPE'] = 'mysqli';
$configValues['DB_HOST'] = 'localhost:/var/run/mysqld/mysqld.sock';
$configValues['DB_PORT'] = '3306';
$configValues['DB_USER'] = 'radius';
$configValues['DB_PASS'] = 'radius';
$configValues['DB_NAME'] = 'radius';
$configValues['CONFIG_FILE_DALORADIUS_VERSION'] = '1.3-master';
$configValues['CONFIG_MAINT_TEST_USER'] = 'administrator';
CONF
done

echo "Starting Apache for daloRADIUS Web Admin UI..."
apache2ctl start

echo "Starting FreeRADIUS service..."
exec freeradius -f -l stdout
