"""Map tiles relayed from OpenStreetMap with an on-disk cache.

Browsers such as Brave strip the Referer header OSM requires, so tiles are
fetched server-side with an identifying User-Agent (as OSM's tile usage
policy asks) and cached, which also spares OSM's volunteer-run servers.

The cache cleans itself: at most once a day, a tile request starts a
background pass that deletes tiles not refreshed for TILE_CACHE_MAX_DAYS.
"""

import logging
import os
import tempfile
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings

UPSTREAM_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
MAX_ZOOM = 19
TIMEOUT_SECONDS = 10
# OSM tiles change rarely: refresh a cached tile after a week.
FRESH_SECONDS = 7 * 24 * 60 * 60
PRUNE_INTERVAL_SECONDS = 24 * 60 * 60

logger = logging.getLogger(__name__)


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


def prune(max_age_days):
    """Delete tiles not refreshed for `max_age_days`, then empty directories. Returns the count."""
    root = settings.TILE_CACHE_DIR
    if not root.exists():
        return 0
    limit = time.time() - max_age_days * 24 * 60 * 60
    removed = 0
    # rglob yields paths one at a time: memory stays flat whatever the cache size.
    for path in root.rglob("*.png"):
        try:
            if path.stat().st_mtime < limit:
                path.unlink()
                removed += 1
        except FileNotFoundError:
            pass  # Replaced or removed concurrently.
    for directory in sorted((p for p in root.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
        try:
            directory.rmdir()  # Only succeeds when empty.
        except OSError:
            pass
    return removed


def _prune_in_background():
    try:
        removed = prune(settings.TILE_CACHE_MAX_DAYS)
        logger.info("Tile cache pruned: %s tile(s) removed", removed)
    except Exception:
        logger.exception("Tile cache pruning failed")


def maybe_prune_async():
    """Start a background pruning pass if none ran in the last day (cost when not due: one stat)."""
    marker = settings.TILE_CACHE_DIR / ".last_prune"
    try:
        if time.time() - marker.stat().st_mtime < PRUNE_INTERVAL_SECONDS:
            return False
    except FileNotFoundError:
        pass
    # Touch the marker first so other workers do not start the same pass.
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.touch()
    threading.Thread(target=_prune_in_background, name="tile-cache-prune", daemon=True).start()
    return True
