"""Vector basemap relayed from OpenFreeMap with an on-disk cache.

The map is drawn in the browser by MapLibre from OpenFreeMap's vector tiles (OpenStreetMap
data): style, TileJSON, tiles, fonts and sprites all come through /tiles/<path>, so the
CSP keeps forbidding third-party origins, members share one cache and upstream servers see
a single identified client. Only the paths a style needs are relayed: this is no open proxy.

Styles: OpenFreeMap's own ("liberty", "dark"), OpenStreetMap Americana ("americana"), whose
style and icons come from americanamap.org but which is wired to OpenFreeMap's tiles (same
OpenMapTiles schema) and fonts, and our own ("night", basemap_styles.py), built here.

The cache cleans itself: at most once a day, a request starts a background pass that
deletes files not refreshed for TILE_CACHE_MAX_DAYS.
"""

import json
import logging
import os
import re
import tempfile
import threading
import time
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from django.conf import settings

from .basemap_styles import LOCAL_STYLES

UPSTREAM = "https://tiles.openfreemap.org/"
AMERICANA = "https://americanamap.org/"
TIMEOUT_SECONDS = 10
PRUNE_INTERVAL_SECONDS = 24 * 60 * 60
PRUNE_MARKER = ".last_prune"
DAY = 24 * 60 * 60

# Americana's fonts are not on OpenFreeMap: the closest ones it has.
AMERICANA_FONTS = {
    "Americana-Regular": "Noto Sans Regular",
    "Americana-Bold": "Noto Sans Bold",
    "Americana-Italic": "Noto Sans Italic",
    "Americana-Bold-Italic": "Noto Sans Bold",
}


@dataclass(frozen=True)
class Resource:
    upstream_url: str
    content_type: str
    # Seconds before refreshing a cached copy.
    fresh_seconds: int
    # "openfreemap": point OpenFreeMap URLs back to the relay; "americana": adapt the style;
    # "local": one of our own styles, built here (nothing to download).
    transform: str | None = None


def _openfreemap(path, content_type, fresh_seconds, transform=None):
    return Resource(UPSTREAM + quote(path, safe="/,@"), content_type, fresh_seconds, transform)


# Relayed paths. Styles and TileJSON point to the current weekly tile set, hence a short
# freshness; tiles live under a versioned path and never change.
ALLOWED = [
    (re.compile(r"styles/(liberty|dark)"), lambda p, m: _openfreemap(p, "application/json", DAY, "openfreemap")),
    (re.compile(r"planet"), lambda p, m: _openfreemap(p, "application/json", DAY, "openfreemap")),
    (re.compile(r"planet/[\w.-]+/\d{1,2}/\d+/\d+\.pbf"), lambda p, m: _openfreemap(p, "application/x-protobuf", 30 * DAY)),
    (re.compile(r"natural_earth/ne2sr/\d{1,2}/\d+/\d+\.png"), lambda p, m: _openfreemap(p, "image/png", 30 * DAY)),
    (
        re.compile(r"sprites/[\w.-]+/ofm(@2x)?\.(json|png)"),
        lambda p, m: _openfreemap(p, "application/json" if p.endswith(".json") else "image/png", 7 * DAY, "openfreemap"),
    ),
    (re.compile(r"fonts/[\w ,-]+/\d+-\d+\.pbf"), lambda p, m: _openfreemap(p, "application/x-protobuf", 30 * DAY)),
    (re.compile(r"styles/(%s)" % "|".join(LOCAL_STYLES)), lambda p, m: Resource("", "application/json", 0, "local")),
    (re.compile(r"styles/americana"), lambda p, m: Resource(AMERICANA + "style.json", "application/json", DAY, "americana")),
    (
        re.compile(r"americana/sprites/(sprite(@2x)?\.(json|png))"),
        lambda p, m: Resource(
            AMERICANA + "sprites/" + m[1], "application/json" if p.endswith(".json") else "image/png", 7 * DAY
        ),
    ),
]

logger = logging.getLogger(__name__)


class TileError(Exception):
    pass


def resolve(path):
    """The Resource behind an allowed path, None otherwise."""
    if ".." in path:
        return None
    for pattern, build in ALLOWED:
        if match := pattern.fullmatch(path):
            return build(path, match)
    return None


def cache_path(path):
    # Allowed paths have no "..": they stay inside the cache directory. Extension-less
    # documents (styles, TileJSON) get one, so a file never shares its name with a directory.
    name = path if "." in path.rsplit("/", 1)[-1] else f"{path}.json"
    return settings.TILE_CACHE_DIR / "basemap" / name


def _download(url):
    request = Request(url, headers={"User-Agent": settings.TILE_USER_AGENT})
    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            if response.status != 200:
                raise TileError(f"Unexpected upstream response {response.status}")
            return response.read()
    except (HTTPError, URLError, TimeoutError) as exc:
        raise TileError(str(exc)) from exc


def _write_atomically(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    # Concurrent requests for the same file must never see a half-written one.
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as tmp:
        tmp.write(data)
    os.replace(tmp.name, path)


def get(path, resource):
    """Bytes of an allowed upstream file, downloading it when missing or stale."""
    if resource.transform == "local":
        return b""
    cached = cache_path(path)
    try:
        if time.time() - cached.stat().st_mtime < resource.fresh_seconds:
            return cached.read_bytes()
    except FileNotFoundError:
        pass
    try:
        data = _download(resource.upstream_url)
    except TileError as exc:
        logger.warning("%s not fetched from %s: %s", path, resource.upstream_url, exc)
        # Upstream unreachable: a stale copy is better than a hole in the map.
        try:
            return cached.read_bytes()
        except FileNotFoundError:
            raise exc from None
    _write_atomically(cached, data)
    return data


def rewrite(data, relay_url):
    """Point the OpenFreeMap URLs of a style or TileJSON to this relay (e.g. https://host/tiles/)."""
    return data.replace(UPSTREAM.encode(), relay_url.encode())


def americana_style(data, relay_url):
    """Americana wired to this relay: OpenFreeMap tiles and fonts, Americana icons, no relief."""
    style = json.loads(data)
    # The relief layer reads elevation tiles from yet another host: left out.
    relief = {name for name, source in style["sources"].items() if source.get("type") == "raster-dem"}
    style["sources"] = {name: source for name, source in style["sources"].items() if name not in relief}
    style["layers"] = [layer for layer in style["layers"] if layer.get("source") not in relief]
    style["sources"]["openmaptiles"] = {"type": "vector", "url": relay_url + "planet"}
    style["sprite"] = relay_url + "americana/sprites/sprite"
    style["glyphs"] = relay_url + "fonts/{fontstack}/{range}.pbf"
    text = json.dumps(style, ensure_ascii=False)
    for font, replacement in AMERICANA_FONTS.items():
        text = text.replace(f'"{font}"', f'"{replacement}"')
    return text.encode()


def adapt(path, data, resource, relay_url):
    """The file as served to the browser (URLs pointing back to the relay)."""
    if resource.transform == "openfreemap":
        return rewrite(data, relay_url)
    if resource.transform == "americana":
        return americana_style(data, relay_url)
    if resource.transform == "local":
        name = path.removeprefix("styles/")
        return json.dumps(LOCAL_STYLES[name](relay_url)).encode()
    return data


def prune(max_age_days):
    """Delete cached files not refreshed for `max_age_days`, then empty directories. Returns the count."""
    root = settings.TILE_CACHE_DIR
    if not root.exists():
        return 0
    limit = time.time() - max_age_days * 24 * 60 * 60
    removed = 0
    # rglob yields paths one at a time: memory stays flat whatever the cache size.
    for path in root.rglob("*"):
        if path.name == PRUNE_MARKER or not path.is_file():
            continue
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
        logger.info("Tile cache pruned: %s file(s) removed", removed)
    except Exception:
        logger.exception("Tile cache pruning failed")


def maybe_prune_async():
    """Start a background pruning pass if none ran in the last day (cost when not due: one stat)."""
    marker = settings.TILE_CACHE_DIR / PRUNE_MARKER
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
