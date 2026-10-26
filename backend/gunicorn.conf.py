"""Gunicorn settings for production (see deploy/README.md)."""

import os

# Caddy forwards requests here; never expose this port publicly. On alwaysdata the address
# comes from the site's IP and PORT (deploy/alwaysdata/start.sh).
bind = os.environ.get("GUNICORN_BIND", "127.0.0.1:8001")
# Lets deploy/alwaysdata/deploy.sh reload the code with a HUP signal.
pidfile = os.environ.get("GUNICORN_PIDFILE") or None
wsgi_app = "config.wsgi:application"

# Threads, not just processes: a tile missing from the cache waits on OpenStreetMap,
# and one slow upstream call must not block every other request.
worker_class = "gthread"
workers = int(os.environ.get("GUNICORN_WORKERS", "2"))
threads = int(os.environ.get("GUNICORN_THREADS", "4"))
timeout = 30
graceful_timeout = 20
# Recycle workers now and then to keep memory in check.
max_requests = 2000
max_requests_jitter = 200

accesslog = "-"
errorlog = "-"
# The proxy that sets X-Forwarded-Proto: Caddy on the same machine, alwaysdata's proxy otherwise.
forwarded_allow_ips = os.environ.get("GUNICORN_FORWARDED_ALLOW_IPS", "127.0.0.1")
