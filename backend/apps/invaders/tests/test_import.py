import datetime

from apps.invaders.models import City, Country, Flash, Invader
from apps.invaders.tests.test_security import InvadersTestCase


def row(name, **extra):
    return {"name": name, "lat": 48.85, "lng": 2.35, "points": 20, **extra}


class ImportCitiesTests(InvadersTestCase):
    def test_unknown_city_is_created_in_france_by_default(self):
        rows = [row("LY_1", city={"name": "Lyon", "prefix": "LY_"}), row("LY_2", city={"name": "Lyon"})]
        preview = self.client_for(self.bob).post("/api/import/preview/", rows, format="json").json()
        self.assertEqual(preview["counts"]["errors"], 0)
        self.assertEqual(preview["cities_to_create"], [{"name": "Lyon", "prefix": "LY", "country": "France"}])
        self.assertEqual(preview["countries_to_create"], [])  # France already exists in team A.
        self.assertFalse(City.objects.filter(prefix="LY").exists())  # Preview writes nothing.

        response = self.client_for(self.bob).post("/api/import/commit/", rows, format="json")
        self.assertEqual(response.json()["cities_created"], 1)
        lyon = City.objects.get(team=self.team_a, prefix="LY")
        self.assertEqual((lyon.name, lyon.country), ("Lyon", self.france))
        self.assertEqual(Invader.objects.filter(city=lyon).count(), 2)

    def test_city_country_is_created_when_given(self):
        rows = [row("AMS_1", city={"name": "Amsterdam", "prefix": "AMS", "country": "Pays-Bas"})]
        self.client_for(self.bob).post("/api/import/commit/", rows, format="json")
        city = City.objects.get(team=self.team_a, prefix="AMS")
        self.assertEqual(city.country.name, "Pays-Bas")
        self.assertEqual(city.country.team, self.team_a)

    def test_country_of_another_team_is_not_reused(self):
        rows = [row("MI_1", city={"name": "Milan", "country": "Italie"})]  # "Italie" belongs to team B.
        self.client_for(self.bob).post("/api/import/commit/", rows, format="json")
        self.assertEqual(Country.objects.get(team=self.team_a, name="Italie").cities.get().name, "Milan")

    def test_existing_city_is_used_and_not_renamed(self):
        self.client_for(self.bob).post("/api/import/commit/", [row("PA_2", city={"name": "Lutèce"})], format="json")
        self.assertEqual(Invader.objects.get(name="PA_2").city, self.paris)
        self.assertEqual(City.objects.get(pk=self.paris.pk).name, "Paris")

    def test_unknown_city_without_description_or_wrong_prefix_is_an_error(self):
        rows = [row("XX_1"), row("YY_1", city={"name": "Y", "prefix": "ZZ"})]
        preview = self.client_for(self.bob).post("/api/import/preview/", rows, format="json").json()
        self.assertEqual([error["name"] for error in preview["errors"]], ["XX_1", "YY_1"])
        response = self.client_for(self.bob).post("/api/import/commit/", rows, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(City.objects.filter(prefix__in=["XX", "YY"]).exists())


class ImportFlashesTests(InvadersTestCase):
    def test_flashed_by_creates_flashes_for_team_members(self):
        rows = [
            row("PA_2", flashed_by=["bob@example.test", {"email": "CAROL@example.test", "flashed_at": "2025-06-01"}]),
        ]
        response = self.client_for(self.admin).post("/api/import/commit/", rows, format="json")
        self.assertEqual(response.json()["flashed"], 2)
        invader = Invader.objects.get(name="PA_2")
        self.assertTrue(Flash.objects.filter(user=self.bob, invader=invader).exists())
        self.assertEqual(Flash.objects.get(user=self.carol, invader=invader).flashed_at, datetime.date(2025, 6, 1))

    def test_existing_flashes_keep_their_date(self):
        rows = [row("PA_1", flashed_by=[{"email": "carol@example.test", "flashed_at": "2025-06-01"}])]
        self.client_for(self.admin).post("/api/import/commit/", rows, format="json")
        self.assertEqual(Flash.objects.get(user=self.carol, invader=self.pa_1).flashed_at, datetime.date(2026, 1, 1))

    def test_unknown_or_other_team_member_is_an_error(self):
        rows = [row("PA_2", flashed_by=["eve@example.test"]), row("PA_3", flashed_by=["nobody@example.test"])]
        response = self.client_for(self.admin).post("/api/import/commit/", rows, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(response.json()["errors"]), 2)
        self.assertFalse(Invader.objects.filter(name__in=["PA_2", "PA_3"]).exists())

    def test_future_flash_date_is_an_error(self):
        rows = [row("PA_2", flashed_by=[{"email": "bob@example.test", "flashed_at": "2999-01-01"}])]
        preview = self.client_for(self.admin).post("/api/import/preview/", rows, format="json").json()
        self.assertEqual(preview["counts"]["errors"], 1)
