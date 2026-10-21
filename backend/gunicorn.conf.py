"""Gunicorn settings for production (see deploy/README.md)."""

import os

# Caddy forwards requests here; never expose this port publicly.
bind = os.environ.get("GUNICORN_BIND", "127.0.0.1:8001")
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
# Caddy runs on the same machine and sets X-Forwarded-Proto.
forwarded_allow_ips = "127.0.0.1"
