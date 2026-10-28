"""Live position of the International Space Station, where the SPACE2ISS invader is.

Fetched server-side from the public Where the ISS at? API (no key; about one request per
second allowed): the CSP forbids third-party origins in the browser, and a short shared cache
means one upstream call every few seconds whatever the number of members watching the map.
"""

import json
import time
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.cache import cache

# 25544 is the ISS NORAD catalog number.
UPSTREAM_URL = "https://api.wheretheiss.at/v1/satellites/25544"
TIMEOUT_SECONDS = 5
# The ISS moves about 40 km in 5 s: fresh enough for a map marker.
CACHE_SECONDS = 5
CACHE_KEY = "iss:position"


class IssError(Exception):
    pass


def position():
    """{"lat", "lng", "altitude_km", "velocity_kmh", "timestamp"} of the ISS right now."""
    if (cached := cache.get(CACHE_KEY)) is not None:
        return cached

    request = Request(UPSTREAM_URL, headers={"User-Agent": settings.GEOCODER_USER_AGENT})
    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            data = json.load(response)
        result = {
            "lat": round(float(data["latitude"]), 4),
            "lng": round(float(data["longitude"]), 4),
            "altitude_km": round(float(data["altitude"])),
            "velocity_kmh": round(float(data["velocity"])),
            "timestamp": int(data.get("timestamp") or time.time()),
        }
    except (URLError, TimeoutError, ValueError, KeyError, TypeError) as exc:
        raise IssError(str(exc)) from exc
    cache.set(CACHE_KEY, result, CACHE_SECONDS)
    return result
