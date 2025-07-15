# Gunicorn configuration for PrivacyIDEA
import multiprocessing
import os

# Server socket
bind = "127.0.0.1:5000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
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
pidfile = "/var/run/privacyidea/privacyidea.pid"
user = "privacyidea"
group = "privacyidea"
tmp_upload_dir = "/tmp"

# SSL (if needed)
keyfile = os.environ.get('SSL_KEYFILE', None)
certfile = os.environ.get('SSL_CERTFILE', None)

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