"""Small fixed-window rate limiter for the views outside DRF (tiles, admin login)."""

import time
from functools import wraps

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse


def client_ip(request):
    """Client IP, trusting X-Forwarded-For only from the NUM_PROXIES proxies in front (Caddy)."""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    proxies = settings.REST_FRAMEWORK.get("NUM_PROXIES") or 0
    if forwarded and proxies:
        hops = [hop.strip() for hop in forwarded.split(",")]
        return hops[-min(proxies, len(hops))]
    return request.META.get("REMOTE_ADDR", "")


def is_allowed(key, limit, window_seconds):
    """Count one hit for `key`; False once `limit` hits happened in the current window."""
    bucket = f"ratelimit:{key}:{int(time.time() // window_seconds)}"
    cache.add(bucket, 0, window_seconds)
    try:
        return cache.incr(bucket) <= limit
    except ValueError:  # Expired between add and incr.
        cache.set(bucket, 1, window_seconds)
        return True


def too_many_requests():
    response = HttpResponse("Trop de requêtes. Réessayez dans une minute.", status=429, content_type="text/plain; charset=utf-8")
    response["Retry-After"] = "60"
    return response


def limit_posts_by_ip(limit, window_seconds, scope):
    """Throttle POST requests per client IP (e.g. login forms)."""

    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if request.method == "POST" and not is_allowed(f"{scope}:{client_ip(request)}", limit, window_seconds):
                return too_many_requests()
            return view(request, *args, **kwargs)

        return wrapped

    return decorator
