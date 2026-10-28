import io
import json
from unittest import mock
from urllib.error import URLError

from django.apps import apps

from apps.accounts.testing import ApiTestCase
from apps.invaders.models import City, Country, Invader
from apps.invaders.naming import parse_name
from apps.invaders.space2iss import add_to_teams

UPSTREAM = {"latitude": 12.345678, "longitude": -45.678912, "altitude": 421.7, "velocity": 27580.4, "timestamp": 1793000000}


def upstream_response():
    return io.BytesIO(json.dumps(UPSTREAM).encode())


class SpecialNameTests(ApiTestCase):
    def test_space2iss_belongs_to_the_space_city(self):
        self.assertEqual(parse_name("SPACE2ISS"), ("SPACE", 2))
        space = City.objects.create(
            team=self.team_a, name="Space", prefix="SPACE", country=Country.objects.create(team=self.team_a, name="Space")
        )
        response = self.client_for(self.bob).post(
            "/api/invaders/", {"name": "space2iss", "lat": 40.4, "lng": -45.7, "points": 100}, format="json"
        )
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(Invader.objects.get(name="SPACE2ISS").city, space)

    def test_other_names_without_prefix_are_still_refused(self):
        self.assertIsNone(parse_name("SPACE2"))


@mock.patch("apps.invaders.iss.urlopen")
class IssPositionTests(ApiTestCase):
    def test_members_get_the_live_position_cached(self, urlopen):
        urlopen.return_value = upstream_response()
        bob = self.client_for(self.bob)
        first = bob.get("/api/iss/")
        second = bob.get("/api/iss/")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json(), {"lat": 12.3457, "lng": -45.6789, "altitude_km": 422, "velocity_kmh": 27580, "timestamp": 1793000000})
        self.assertEqual(second.json(), first.json())
        self.assertEqual(urlopen.call_count, 1)

    def test_upstream_failure_gives_a_french_502(self, urlopen):
        urlopen.side_effect = URLError("down")
        response = self.client_for(self.bob).get("/api/iss/")
        self.assertEqual(response.status_code, 502)
        self.assertIn("ISS", response.json()["detail"])

    def test_anonymous_is_refused(self, urlopen):
        self.assertEqual(self.client_for().get("/api/iss/").status_code, 403)
        urlopen.assert_not_called()


class Space2IssMigrationTests(ApiTestCase):
    def test_adds_the_invader_once_per_team(self):
        add_to_teams(apps)
        add_to_teams(apps)
        for team in (self.team_a, self.team_b):
            invader = Invader.objects.get(team=team, name="SPACE2ISS")
            self.assertEqual((invader.city.name, invader.city.prefix, invader.city.country.name), ("Space", "SPACE", "Space"))
            self.assertEqual((invader.points, invader.comment), (100, "To infinity… and beyond"))
            self.assertTrue(invader.image.name.startswith("invaders/"))
            self.assertEqual(invader.history.count(), 1)
        self.assertEqual(Invader.objects.filter(name="SPACE2ISS").count(), 2)

    def test_reuses_an_existing_space_city(self):
        space = City.objects.create(
            team=self.team_a, name="Espace", prefix="SPACE", country=Country.objects.create(team=self.team_a, name="Cosmos")
        )
        add_to_teams(apps, [self.team_a])
        self.assertEqual(Invader.objects.get(team=self.team_a, name="SPACE2ISS").city, space)
