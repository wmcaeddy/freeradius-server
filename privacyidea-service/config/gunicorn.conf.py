# Gunicorn configuration for PrivacyIDEA on Railway.com
import multiprocessing
import os

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = min(multiprocessing.cpu_count() * 2 + 1, 4)  # Limit for Railway
worker_class = "sync"
worker_connections = 1000
timeout = 300
keepalive = 2
max_requests = 1000
max_requests_jitter = 50

# Logging
loglevel = "info"
accesslog = "/var/log/privacyidea/access.log"
errorlog = "/var/log/privacyidea/error.log"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "privacyidea"

# Server mechanics
daemon = False
pidfile = "/var/run/privacyidea.pid"
user = "privacyidea"
group = "privacyidea"
tmp_upload_dir = "/tmp"

# Environment
raw_env = [
    'PRIVACYIDEA_CONFIGFILE=/etc/privacyidea/pi.cfg',
]

# Preload application
preload_app = True

# Security
forwarded_allow_ips = '*'
secure_scheme_headers = {
    'X-FORWARDED-PROTO': 'https',
    'X-FORWARDED-SSL': 'on'
}