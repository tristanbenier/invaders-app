"""Our own MapLibre styles for the OpenFreeMap tiles (OpenMapTiles schema).

One layout, two palettes, both modeled on Brave Search's map of Nantes:
- "night" (dark theme): navy land, darker water, teal parks and thin slate roads;
- "day" (light theme): near-white land, cyan water, pale green parks and gray-blue roads.
Place names in spaced capitals, a few landmarks in light or dark text, hospitals and parks
tinted. No icons, so the invader markers stay the most visible thing on the map.
"""

NIGHT = {
    "land": "#1e2a3b",
    "water": "#111b2a",
    "park": "#1c4448",
    "park_opacity": 0.7,
    "building": "#233246",
    "hospital": "#3a2733",
    "industrial": None,
    "road_minor": "#324257",
    "road_medium": "#3c4e66",
    "road_major": "#4a5e79",
    "rail": "#3a4a61",
    "label_place": "#8a95a6",
    "label_city": "#c9d1dc",
    "label_water": "#7a8aa0",
    "label_road": "#7f8b9c",
    "label_poi": "#c3cbd6",
    "label_hospital": "#e8737a",
    "label_park": "#6fcf8a",
    "label_culture": None,
    "label_halo": "#1a2433",
}

DAY = {
    "land": "#f5f6f7",
    "water": "#8fd4ea",
    "park": "#c6eac3",
    "park_opacity": 0.9,
    "building": "#eaecef",
    "hospital": "#fbe1e1",
    "industrial": "#e3e5e8",
    "road_minor": "#d0d6de",
    "road_medium": "#bcc5d0",
    "road_major": "#aab5c3",
    "rail": "#c3c9d1",
    "label_place": "#3e4752",
    "label_city": "#2a323c",
    "label_water": "#4f8aa0",
    "label_road": "#6b7480",
    "label_poi": "#3d4652",
    "label_hospital": "#dc4c5a",
    "label_park": "#2f9e5b",
    "label_culture": "#6a5ad8",
    "label_halo": "#ffffff",
}

FONT = ["Noto Sans Regular"]
FONT_BOLD = ["Noto Sans Bold"]
FONT_ITALIC = ["Noto Sans Italic"]

MINOR_CLASSES = ["minor", "service", "track", "path"]
MEDIUM_CLASSES = ["secondary", "tertiary"]
MAJOR_CLASSES = ["motorway", "trunk", "primary"]
# Landmarks whose label takes the "label_culture" color (castles, museums...).
CULTURE_CLASSES = ["castle", "museum", "attraction", "monument", "art_gallery"]

NAME = ["coalesce", ["get", "name:fr"], ["get", "name"]]


def _width(*stops):
    """Line width interpolated on the zoom: _width(12, 0.5, 18, 6)."""
    return ["interpolate", ["exponential", 1.5], ["zoom"], *stops]


def _roads(classes, color, width, layer_id, minzoom=0):
    return {
        "id": layer_id,
        "type": "line",
        "source": "openmaptiles",
        "source-layer": "transportation",
        "minzoom": minzoom,
        "filter": ["all", ["in", ["get", "class"], ["literal", classes]], ["!=", ["get", "brunnel"], "tunnel"]],
        "layout": {"line-cap": "round", "line-join": "round"},
        "paint": {"line-color": color, "line-width": width},
    }


def _symbol(palette, layer_id, source_layer, filter_, layout, paint, minzoom=0, maxzoom=24):
    return {
        "id": layer_id,
        "type": "symbol",
        "source": "openmaptiles",
        "source-layer": source_layer,
        "minzoom": minzoom,
        "maxzoom": maxzoom,
        "filter": filter_,
        "layout": layout,
        "paint": {"text-halo-color": palette["label_halo"], "text-halo-width": 1.2, **paint},
    }


def _poi_color(palette):
    colors = ["match", ["get", "class"], "hospital", palette["label_hospital"], ["park", "garden"], palette["label_park"]]
    if palette["label_culture"]:
        colors += [CULTURE_CLASSES, palette["label_culture"]]
    return [*colors, palette["label_poi"]]


def _style(name, palette, relay_url):
    p = palette
    fills = [
        {"id": "background", "type": "background", "paint": {"background-color": p["land"]}},
    ]
    if p["industrial"]:
        fills.append(
            {
                "id": "landuse-industrial",
                "type": "fill",
                "source": "openmaptiles",
                "source-layer": "landuse",
                "filter": ["in", ["get", "class"], ["literal", ["industrial", "railway", "commercial", "retail"]]],
                "paint": {"fill-color": p["industrial"]},
            }
        )
    fills += [
        {
            "id": "landcover-green",
            "type": "fill",
            "source": "openmaptiles",
            "source-layer": "landcover",
            "filter": ["in", ["get", "class"], ["literal", ["grass", "wood", "farmland", "wetland"]]],
            "paint": {"fill-color": p["park"], "fill-opacity": p["park_opacity"]},
        },
        {
            "id": "park",
            "type": "fill",
            "source": "openmaptiles",
            "source-layer": "park",
            "paint": {"fill-color": p["park"]},
        },
        {
            "id": "landuse-green",
            "type": "fill",
            "source": "openmaptiles",
            "source-layer": "landuse",
            "filter": ["in", ["get", "class"], ["literal", ["cemetery", "pitch", "stadium", "garden"]]],
            "paint": {"fill-color": p["park"], "fill-opacity": 0.8},
        },
        {
            "id": "landuse-hospital",
            "type": "fill",
            "source": "openmaptiles",
            "source-layer": "landuse",
            "filter": ["==", ["get", "class"], "hospital"],
            "paint": {"fill-color": p["hospital"]},
        },
        {
            "id": "water",
            "type": "fill",
            "source": "openmaptiles",
            "source-layer": "water",
            "paint": {"fill-color": p["water"]},
        },
        {
            "id": "waterway",
            "type": "line",
            "source": "openmaptiles",
            "source-layer": "waterway",
            "paint": {"line-color": p["water"], "line-width": _width(10, 0.5, 18, 4)},
        },
        {
            "id": "building",
            "type": "fill",
            "source": "openmaptiles",
            "source-layer": "building",
            "minzoom": 14,
            "paint": {"fill-color": p["building"], "fill-opacity": ["interpolate", ["linear"], ["zoom"], 14, 0, 16, 0.9]},
        },
    ]
    lines = [
        {
            "id": "tunnel",
            "type": "line",
            "source": "openmaptiles",
            "source-layer": "transportation",
            "minzoom": 13,
            "filter": ["==", ["get", "brunnel"], "tunnel"],
            "layout": {"line-join": "round"},
            "paint": {"line-color": p["road_minor"], "line-width": _width(13, 0.5, 18, 4), "line-dasharray": [2, 2]},
        },
        _roads(MINOR_CLASSES, p["road_minor"], _width(12, 0.3, 18, 5), "road-minor", minzoom=12),
        _roads(MEDIUM_CLASSES, p["road_medium"], _width(9, 0.5, 18, 8), "road-medium", minzoom=9),
        _roads(MAJOR_CLASSES, p["road_major"], _width(5, 0.5, 18, 11), "road-major"),
        {
            "id": "railway",
            "type": "line",
            "source": "openmaptiles",
            "source-layer": "transportation",
            "minzoom": 11,
            "filter": ["in", ["get", "class"], ["literal", ["rail", "transit"]]],
            "paint": {"line-color": p["rail"], "line-width": _width(11, 0.5, 18, 2), "line-dasharray": [3, 2]},
        },
        {
            "id": "boundary-country",
            "type": "line",
            "source": "openmaptiles",
            "source-layer": "boundary",
            "filter": ["all", ["<=", ["get", "admin_level"], 2], ["!=", ["get", "maritime"], 1]],
            "paint": {"line-color": p["road_major"], "line-width": 1, "line-dasharray": [4, 3]},
        },
    ]
    labels = [
        _symbol(
            p,
            "water-name-line",
            "waterway",
            ["has", "name"],
            {
                "text-field": NAME,
                "text-font": FONT_ITALIC,
                "text-size": 13,
                "text-letter-spacing": 0.1,
                "symbol-placement": "line",
            },
            {"text-color": p["label_water"]},
            minzoom=12,
        ),
        _symbol(
            p,
            "water-name",
            "water_name",
            ["has", "name"],
            {"text-field": NAME, "text-font": FONT_ITALIC, "text-size": 13, "text-letter-spacing": 0.1},
            {"text-color": p["label_water"]},
        ),
        _symbol(
            p,
            "road-name",
            "transportation_name",
            ["has", "name"],
            {"text-field": NAME, "text-font": FONT, "text-size": 11, "symbol-placement": "line"},
            {"text-color": p["label_road"]},
            minzoom=15,
        ),
        _symbol(
            p,
            "poi",
            "poi",
            ["all", ["has", "name"], ["<=", ["get", "rank"], 10]],
            {"text-field": NAME, "text-font": FONT, "text-size": 13, "text-max-width": 9},
            {"text-color": _poi_color(p)},
            minzoom=14,
        ),
        _symbol(
            p,
            "place-neighbourhood",
            "place",
            ["in", ["get", "class"], ["literal", ["suburb", "quarter", "neighbourhood"]]],
            {
                "text-field": NAME,
                "text-font": FONT,
                "text-size": ["interpolate", ["linear"], ["zoom"], 12, 11, 16, 15],
                "text-transform": "uppercase",
                "text-letter-spacing": 0.12,
                "text-max-width": 8,
            },
            {"text-color": p["label_place"]},
            minzoom=12,
        ),
        _symbol(
            p,
            "place-village",
            "place",
            ["in", ["get", "class"], ["literal", ["village", "hamlet", "isolated_dwelling"]]],
            {"text-field": NAME, "text-font": FONT, "text-size": 13},
            {"text-color": p["label_place"]},
            minzoom=10,
        ),
        _symbol(
            p,
            "place-city",
            "place",
            ["in", ["get", "class"], ["literal", ["city", "town"]]],
            {
                "text-field": NAME,
                "text-font": FONT_BOLD,
                "text-size": ["interpolate", ["linear"], ["zoom"], 4, 12, 12, 20],
            },
            {"text-color": p["label_city"]},
            maxzoom=13,
        ),
        _symbol(
            p,
            "place-country",
            "place",
            ["==", ["get", "class"], "country"],
            {"text-field": NAME, "text-font": FONT_BOLD, "text-size": 14, "text-transform": "uppercase"},
            {"text-color": p["label_place"]},
            maxzoom=7,
        ),
    ]
    return {
        "version": 8,
        "name": name,
        "sources": {"openmaptiles": {"type": "vector", "url": relay_url + "planet"}},
        "glyphs": relay_url + "fonts/{fontstack}/{range}.pbf",
        "layers": fills + lines + labels,
    }


def night_style(relay_url):
    """The dark theme, its tiles and fonts served by the relay at `relay_url` (…/tiles/)."""
    return _style("Invaders night", NIGHT, relay_url)


def day_style(relay_url):
    """The light theme, its tiles and fonts served by the relay at `relay_url` (…/tiles/)."""
    return _style("Invaders day", DAY, relay_url)


LOCAL_STYLES = {"night": night_style, "day": day_style}
