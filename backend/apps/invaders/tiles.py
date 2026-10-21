"""Map tiles relayed from OpenStreetMap with an on-disk cache.

Browsers such as Brave strip the Referer header OSM requires, so tiles are
fetched server-side with an identifying User-Agent (as OSM's tile usage
policy asks) and cached, which also spares OSM's volunteer-run servers.
"""

import os
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings

UPSTREAM_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
MAX_ZOOM = 19
TIMEOUT_SECONDS = 10
# OSM tiles change rarely: refresh a cached tile after a week.
FRESH_SECONDS = 7 * 24 * 60 * 60


class TileError(Exception):
    pass


def is_valid(z, x, y):
    return 0 <= z <= MAX_ZOOM and 0 <= x < 2**z and 0 <= y < 2**z


def cache_path(z, x, y):
    return settings.TILE_CACHE_DIR / str(z) / str(x) / f"{y}.png"


def _download(z, x, y):
    request = Request(UPSTREAM_URL.format(z=z, x=x, y=y), headers={"User-Agent": settings.TILE_USER_AGENT})
    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            if response.status != 200 or response.headers.get_content_type() != "image/png":
                raise TileError(f"Unexpected upstream response {response.status}")
            # OSM's "Access blocked" image comes as a 200 PNG marked no-cache; real tiles
            # carry a max-age. Never cache the former.
            if "no-cache" in response.headers.get("Cache-Control", ""):
                raise TileError("Upstream refused the request (blocked tile)")
            return response.read()
    except (HTTPError, URLError, TimeoutError) as exc:
        raise TileError(str(exc)) from exc


def _write_atomically(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    # Concurrent requests for the same tile must never see a half-written file.
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as tmp:
        tmp.write(data)
    os.replace(tmp.name, path)


def get_tile(z, x, y):
    """Path to a cached PNG tile, downloading it when missing or stale."""
    path = cache_path(z, x, y)
    is_cached = path.is_file()
    if is_cached and time.time() - path.stat().st_mtime < FRESH_SECONDS:
        return path
    try:
        _write_atomically(path, _download(z, x, y))
    except TileError:
        # OSM unreachable: a stale tile is better than a hole in the map.
        if is_cached:
            return path
        raise
    return path
