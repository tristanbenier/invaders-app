"""Middlewares for hosts without a reverse proxy of our own (e.g. alwaysdata, see deploy/).

Caddy (deploy/Caddyfile) also caps request bodies, but these work behind any front server.
"""

from django.conf import settings
from django.http import HttpResponse

# Scripts, styles, images and API calls only from this site; no framing. Leaflet sets inline
# styles, hence 'unsafe-inline' for styles only.
CONTENT_SECURITY_POLICY = "; ".join(
    [
        "default-src 'self'",
        "script-src 'self'",
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data: blob:",
        "connect-src 'self' blob:",
        "worker-src 'self'",
        "manifest-src 'self'",
        "font-src 'self'",
        "frame-ancestors 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "object-src 'none'",
    ]
)
# Geolocation for the map; camera for photo uploads; nothing else.
PERMISSIONS_POLICY = "geolocation=(self), camera=(self), microphone=(), payment=(), usb=()"


def client_ip_middleware(get_response):
    """Take the client IP from the header set by the host's proxy (CLIENT_IP_HEADER).

    Behind alwaysdata's proxy REMOTE_ADDR is the proxy itself: without this, every visitor
    would share one throttling bucket. Only set it behind a proxy that writes this header
    itself: otherwise a client could pick its own IP and dodge the throttles.
    """

    def middleware(request):
        header = settings.CLIENT_IP_HEADER
        value = request.META.get("HTTP_" + header.upper().replace("-", "_")) if header else None
        if value:
            request.META["REMOTE_ADDR"] = value.strip()
        return get_response(request)

    return middleware


def request_size_middleware(get_response):
    """Refuse bodies over MAX_REQUEST_BODY_MB before Django reads them (photos are at most 10 MB)."""

    def middleware(request):
        limit = settings.MAX_REQUEST_BODY_MB * 1024 * 1024
        try:
            length = int(request.META.get("CONTENT_LENGTH") or 0)
        except ValueError:
            length = 0
        if length > limit:
            return HttpResponse("Fichier trop volumineux.", status=413, content_type="text/plain; charset=utf-8")
        return get_response(request)

    return middleware


def security_headers_middleware(get_response):
    """Content-Security-Policy and Permissions-Policy (enabled by SECURITY_HEADERS).

    Not on the Django admin, which may rely on inline scripts.
    """

    def middleware(request):
        response = get_response(request)
        if settings.SECURITY_HEADERS:
            if not request.path.startswith("/admin/"):
                response.headers.setdefault("Content-Security-Policy", CONTENT_SECURITY_POLICY)
            response.headers.setdefault("Permissions-Policy", PERMISSIONS_POLICY)
        return response

    return middleware
