"""Geocoding through Nominatim (OpenStreetMap).

Nominatim's usage policy asks for an identifying User-Agent, at most one
request per second and no search-as-you-type: results are cached, calls are
throttled per user and the app only searches addresses on explicit submit.
"""

import hashlib
import json
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.cache import cache

BASE_URL = "https://nominatim.openstreetmap.org"
SEARCH_LIMIT = 5
TIMEOUT_SECONDS = 6
CACHE_SECONDS = 30 * 24 * 60 * 60
# Street-like keys, in order of preference, when there is no "road".
STREET_KEYS = ["road", "pedestrian", "footway", "path", "square", "place"]


class GeocodingError(Exception):
    pass


def _address_line(address):
    street = next((address[key] for key in STREET_KEYS if address.get(key)), "")
    number = address.get("house_number", "")
    return f"{number} {street}".strip()


def _city(address):
    return address.get("city") or address.get("town") or address.get("village") or address.get("municipality") or ""


def _fetch(path, params):
    query = urlencode({"format": "jsonv2", "addressdetails": 1, "accept-language": "fr", **params})
    request = Request(f"{BASE_URL}/{path}?{query}", headers={"User-Agent": settings.GEOCODER_USER_AGENT})
    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return json.load(response)
    except (URLError, TimeoutError, ValueError) as exc:
        raise GeocodingError(str(exc)) from exc


def reverse(lat, lng):
    """Return {"address1", "zip", "city"} for a point; empty strings when unknown."""
    # ~1 m precision is plenty and makes nearby lookups hit the cache.
    key = f"geocode:reverse:{lat:.5f}:{lng:.5f}"
    if (cached := cache.get(key)) is not None:
        return cached

    address = _fetch("reverse", {"lat": f"{lat:.6f}", "lon": f"{lng:.6f}", "zoom": 18}).get("address") or {}
    result = {"address1": _address_line(address), "zip": address.get("postcode", ""), "city": _city(address)}
    cache.set(key, result, CACHE_SECONDS)
    return result


def _label(place):
    """Short label: "2 Place Saint-Jean, 44000 Nantes", falling back on Nominatim's long name."""
    address = place.get("address") or {}
    street = place.get("name") or _address_line(address)
    locality = " ".join(part for part in (address.get("postcode", ""), _city(address)) if part)
    if street and locality:
        return f"{street}, {locality}"
    return ", ".join(place.get("display_name", "").split(", ")[:3])


def search(text, near=None):
    """Up to SEARCH_LIMIT places matching `text`, biased towards `near` (lat, lng) when given."""
    text = " ".join(text.split())
    params = {"q": text, "limit": SEARCH_LIMIT}
    if near:
        # Rounded so that small map moves still hit the cache.
        lat, lng = round(near[0], 1), round(near[1], 1)
        # Prefer results around the map center without excluding the rest of the world.
        params["viewbox"] = f"{lng - 0.5:.4f},{lat + 0.5:.4f},{lng + 0.5:.4f},{lat - 0.5:.4f}"
        params["bounded"] = 0
    digest = hashlib.sha1(urlencode(params).lower().encode()).hexdigest()
    key = f"geocode:search:{digest}"
    if (cached := cache.get(key)) is not None:
        return cached

    results = [
        {"label": _label(place), "lat": float(place["lat"]), "lng": float(place["lon"])}
        for place in _fetch("search", params)
        if "lat" in place and "lon" in place
    ]
    cache.set(key, results, CACHE_SECONDS)
    return results
