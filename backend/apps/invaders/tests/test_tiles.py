import io
import json
from unittest import mock

from django.test import Client

from apps.accounts.testing import ApiTestCase
from apps.invaders import tiles

STYLE = {"sources": {"openmaptiles": {"type": "vector", "url": "https://tiles.openfreemap.org/planet"}}, "layers": []}


def upstream(body):
    response = io.BytesIO(body)
    response.status = 200
    return response


@mock.patch("apps.invaders.tiles.urlopen")
class BasemapRelayTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.browser = Client()
        self.browser.force_login(self.bob)

    def test_style_urls_point_back_to_the_relay(self, urlopen):
        urlopen.return_value = upstream(json.dumps(STYLE).encode())
        response = self.browser.get("/tiles/styles/dark")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(response.json()["sources"]["openmaptiles"]["url"], "http://testserver/tiles/planet")

    def test_tiles_are_cached_on_disk(self, urlopen):
        urlopen.return_value = upstream(b"tile-bytes")
        for _ in range(2):
            response = self.browser.get("/tiles/planet/20261101_080013_pt/14/8170/5676.pbf")
            self.assertEqual(response.content, b"tile-bytes")
        self.assertEqual(response["Content-Type"], "application/x-protobuf")
        self.assertEqual(urlopen.call_count, 1)

    def test_fonts_keep_their_spaces_upstream(self, urlopen):
        urlopen.return_value = upstream(b"glyphs")
        self.assertEqual(self.browser.get("/tiles/fonts/Noto Sans Regular/0-255.pbf").status_code, 200)
        self.assertEqual(urlopen.call_args.args[0].full_url, "https://tiles.openfreemap.org/fonts/Noto%20Sans%20Regular/0-255.pbf")

    def test_only_basemap_paths_are_relayed(self, urlopen):
        for path in ["styles/bright", "planet/../../etc/passwd", "admin/", "planet/x/14/1/2.png"]:
            with self.subTest(path=path):
                self.assertEqual(self.browser.get(f"/tiles/{path}").status_code, 404)
        urlopen.assert_not_called()

    def test_americana_uses_the_relayed_tiles_fonts_and_icons(self, urlopen):
        americana = {
            "sources": {
                "openmaptiles": {"type": "vector", "url": "https://tiles.openstreetmap.us/vector/openmaptiles.json"},
                "dem": {"type": "raster-dem", "tiles": ["https://example.com/{z}/{x}/{y}.png"]},
            },
            "sprite": "https://americanamap.org/sprites/sprite",
            "glyphs": "https://font.americanamap.org/{fontstack}/{range}.pbf",
            "layers": [
                {"id": "label", "source": "openmaptiles", "layout": {"text-font": ["Americana-Bold"]}},
                {"id": "hillshading", "type": "hillshade", "source": "dem"},
            ],
        }
        urlopen.return_value = upstream(json.dumps(americana).encode())
        style = self.browser.get("/tiles/styles/americana").json()
        self.assertEqual(style["sources"], {"openmaptiles": {"type": "vector", "url": "http://testserver/tiles/planet"}})
        self.assertEqual(style["sprite"], "http://testserver/tiles/americana/sprites/sprite")
        self.assertEqual(style["glyphs"], "http://testserver/tiles/fonts/{fontstack}/{range}.pbf")
        self.assertEqual([layer["id"] for layer in style["layers"]], ["label"])
        self.assertEqual(style["layers"][0]["layout"]["text-font"], ["Noto Sans Bold"])

    def test_day_and_night_styles_are_built_here(self, urlopen):
        for name in ("day", "night"):
            with self.subTest(name=name):
                style = self.browser.get(f"/tiles/styles/{name}").json()
                self.assertEqual(style["sources"]["openmaptiles"]["url"], "http://testserver/tiles/planet")
                self.assertEqual(style["glyphs"], "http://testserver/tiles/fonts/{fontstack}/{range}.pbf")
        urlopen.assert_not_called()

    def test_stale_copy_is_served_when_openfreemap_is_down(self, urlopen):
        path = "planet/v1/3/4/2.pbf"
        cached = tiles.cache_path(path)
        cached.parent.mkdir(parents=True)
        cached.write_bytes(b"old-tile")
        with mock.patch("apps.invaders.tiles.time.time", return_value=cached.stat().st_mtime + 365 * 24 * 3600):
            urlopen.side_effect = tiles.URLError("down")
            self.assertEqual(self.browser.get(f"/tiles/{path}").content, b"old-tile")
