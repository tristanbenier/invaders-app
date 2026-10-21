from unittest import mock

from django.test import Client, override_settings
from rest_framework.settings import api_settings
from rest_framework.test import APIClient
from rest_framework.throttling import SimpleRateThrottle

from apps.accounts.testing import ApiTestCase

# Small limits keep the tests fast; the real values live in settings.REST_FRAMEWORK.
TEST_RATES = {**api_settings.DEFAULT_THROTTLE_RATES, "anon": "3/min", "invitations": "2/hour", "import": "2/hour"}


@mock.patch.object(SimpleRateThrottle, "THROTTLE_RATES", TEST_RATES)
class ApiThrottlingTests(ApiTestCase):
    def test_anonymous_requests_have_a_global_limit(self):
        codes = [APIClient().get("/api/auth/csrf/").status_code for _ in range(4)]
        self.assertEqual(codes, [204, 204, 204, 429])

    def test_creating_invitations_is_limited(self):
        bob = self.client_for(self.bob)
        codes = [bob.post("/api/invitations/", {}, format="json").status_code for _ in range(3)]
        self.assertEqual(codes, [201, 201, 429])

    def test_listing_invitations_is_not_limited_by_the_scope(self):
        bob = self.client_for(self.bob)
        self.assertTrue(all(bob.get("/api/invitations/").status_code == 200 for _ in range(4)))

    def test_import_is_limited(self):
        bob = self.client_for(self.bob)
        rows = [{"name": "PA_1", "lat": 1, "lng": 1, "points": 10}]
        codes = [bob.post("/api/import/preview/", rows, format="json").status_code for _ in range(3)]
        self.assertEqual(codes[-1], 429)

    def test_behind_a_proxy_each_client_ip_has_its_own_bucket(self):
        with mock.patch.object(api_settings, "NUM_PROXIES", 1):
            codes = [
                APIClient().get("/api/auth/csrf/", REMOTE_ADDR="127.0.0.1", HTTP_X_FORWARDED_FOR=f"203.0.113.{i}").status_code
                for i in range(6)
            ]
        self.assertEqual(codes, [204] * 6)


class TileThrottlingTests(ApiTestCase):
    @override_settings(TILE_RATE_LIMIT_PER_MINUTE=5)
    def test_tiles_are_limited_per_member(self):
        browser = Client()
        browser.force_login(self.bob)
        # Zoom 99 is invalid: answered with a 404 without calling OpenStreetMap.
        codes = [browser.get("/tiles/99/0/0.png").status_code for _ in range(7)]
        self.assertEqual(codes, [404] * 5 + [429, 429])
