#!/bin/bash
set -e

mkdir -p /app/data/freeradius/logs /app/data/freeradius/config /app/data/freeradius/certs

echo "Starting FreeRADIUS service..."

if command -v nginx > /dev/null 2>&1; then
    nginx &
fi

exec freeradius -f -l stdout
