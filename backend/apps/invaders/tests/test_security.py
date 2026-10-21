import datetime
import io

from django.test import Client
from PIL import Image
from rest_framework.test import APIClient

from apps.accounts.testing import ApiTestCase
from apps.invaders.models import City, Country, Flash, Invader


class InvadersTestCase(ApiTestCase):
    """Adds Paris (team A) and Rome (team B), one invader each, and a flash by Carol."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.france = Country.objects.create(team=cls.team_a, name="France")
        cls.italy = Country.objects.create(team=cls.team_b, name="Italie")
        cls.paris = City.objects.create(team=cls.team_a, name="Paris", prefix="PA", country=cls.france)
        cls.rome = City.objects.create(team=cls.team_b, name="Rome", prefix="ROM", country=cls.italy)
        cls.pa_1 = Invader.objects.create(team=cls.team_a, name="PA_1", city=cls.paris, lat=48.8, lng=2.3, points=10)
        cls.rom_1 = Invader.objects.create(team=cls.team_b, name="ROM_1", city=cls.rome, lat=41.9, lng=12.5, points=10)
        cls.carol_flash = Flash.objects.create(user=cls.carol, invader=cls.pa_1, flashed_at=datetime.date(2026, 1, 1))


class FlashOwnershipTests(InvadersTestCase):
    def test_flashing_does_not_change_another_members_flash(self):
        self.client_for(self.bob).post(f"/api/invaders/{self.pa_1.pk}/flash/", {"flashed_at": "2026-02-02"}, format="json")
        self.carol_flash.refresh_from_db()
        self.assertEqual(self.carol_flash.flashed_at, datetime.date(2026, 1, 1))

    def test_unflashing_does_not_delete_another_members_flash(self):
        self.client_for(self.bob).delete(f"/api/invaders/{self.pa_1.pk}/flash/")
        self.assertTrue(Flash.objects.filter(pk=self.carol_flash.pk).exists())

    def test_flash_payload_cannot_target_another_user(self):
        self.client_for(self.bob).post(
            f"/api/invaders/{self.pa_1.pk}/flash/", {"user": self.carol.pk, "flashed_at": "2026-03-03"}, format="json"
        )
        self.carol_flash.refresh_from_db()
        self.assertEqual(self.carol_flash.flashed_at, datetime.date(2026, 1, 1))
        self.assertTrue(Flash.objects.filter(user=self.bob, invader=self.pa_1).exists())

    def test_my_flashes_lists_only_mine(self):
        flashes = self.client_for(self.bob).get("/api/flashes/").json()
        self.assertEqual(flashes, [])


class TeamIsolationTests(InvadersTestCase):
    def test_other_team_invader_is_invisible(self):
        eve = self.client_for(self.eve)
        self.assertNotIn(self.pa_1.pk, [invader["id"] for invader in eve.get("/api/invaders/").json()])
        for method, url in [
            ("get", f"/api/invaders/{self.pa_1.pk}/"),
            ("patch", f"/api/invaders/{self.pa_1.pk}/"),
            ("post", f"/api/invaders/{self.pa_1.pk}/flash/"),
            ("get", f"/api/invaders/{self.pa_1.pk}/history/"),
            ("get", f"/api/cities/{self.paris.pk}/"),
            ("patch", f"/api/countries/{self.france.pk}/"),
        ]:
            with self.subTest(method=method, url=url):
                self.assertEqual(getattr(eve, method)(url, {}, format="json").status_code, 404)

    def test_city_cannot_use_another_teams_country(self):
        bob = self.client_for(self.bob)
        response = bob.post("/api/cities/", {"name": "Roma", "prefix": "RX", "country": self.italy.pk}, format="json")
        self.assertEqual(response.status_code, 400)
        bob.patch(f"/api/cities/{self.paris.pk}/", {"country": self.italy.pk}, format="json")
        self.assertEqual(City.objects.get(pk=self.paris.pk).country, self.france)

    def test_filters_and_stats_stay_in_the_team(self):
        bob = self.client_for(self.bob)
        self.assertEqual(bob.get(f"/api/invaders/?flashed_by={self.eve.pk}").json(), [])
        self.assertEqual(self.client_for(self.eve).get("/api/stats/team/").json()["invaders"], 1)

    def test_import_cannot_touch_another_teams_invader(self):
        self.client_for(self.bob).post(
            "/api/import/commit/", [{"name": "ROM_1", "lat": 1, "lng": 1, "points": 99}], format="json"
        )
        self.rom_1.refresh_from_db()
        self.assertEqual(self.rom_1.points, 10)


class InvaderWriteTests(InvadersTestCase):
    def test_team_city_and_author_are_not_writable(self):
        self.client_for(self.bob).patch(
            f"/api/invaders/{self.pa_1.pk}/",
            {"team": self.team_b.pk, "city": self.rome.pk, "created_by": self.eve.pk},
            format="json",
        )
        self.pa_1.refresh_from_db()
        self.assertEqual((self.pa_1.team, self.pa_1.city, self.pa_1.created_by), (self.team_a, self.paris, None))

    def test_deletions_are_reserved_to_admins(self):
        bob = self.client_for(self.bob)
        self.assertEqual(bob.delete(f"/api/invaders/{self.pa_1.pk}/").status_code, 403)
        self.assertEqual(bob.delete(f"/api/cities/{self.paris.pk}/").status_code, 403)

    def test_absurd_points_and_huge_comment_are_refused(self):
        bob = self.client_for(self.bob)
        url = f"/api/invaders/{self.pa_1.pk}/"
        self.assertEqual(bob.patch(url, {"points": 2_000_000_000}, format="json").status_code, 400)
        self.assertEqual(bob.patch(url, {"comment": "x" * 100_000}, format="json").status_code, 400)

    def test_decompression_bomb_is_refused(self):
        bomb = io.BytesIO()
        Image.new("1", (12000, 12000)).save(bomb, "PNG")
        bomb.name = "bomb.png"
        bomb.seek(0)
        response = self.client_for(self.bob).patch(f"/api/invaders/{self.pa_1.pk}/", {"image": bomb}, format="multipart")
        self.assertEqual(response.status_code, 400)
        self.assertIn("image", response.json())


class AnonymousAccessTests(InvadersTestCase):
    def test_api_and_tiles_require_a_member(self):
        anonymous = APIClient()
        for url in ["/api/invaders/", "/api/stats/me/", "/api/flashes/", "/api/cities/", "/api/geocode/search/?q=paris"]:
            with self.subTest(url=url):
                self.assertEqual(anonymous.get(url).status_code, 403)
        self.assertEqual(Client().get("/tiles/13/4149/2817.png").status_code, 403)
