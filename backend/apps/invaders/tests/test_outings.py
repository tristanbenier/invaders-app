import datetime

from apps.invaders import outings
from apps.invaders.models import Flash, Invader, Outing, Status
from apps.invaders.tests.test_security import InvadersTestCase

# Around Paris town hall; PA_1 of the fixture is about 6 km away.
START = {"start_lat": 48.8566, "start_lng": 2.3522}


class OutingTests(InvadersTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # A line of invaders a few hundred metres apart, heading north from the start.
        cls.line = [
            Invader.objects.create(
                team=cls.team_a, name=f"PA_{10 + i}", city=cls.paris, lat=48.8566 + 0.003 * i, lng=2.3522, points=10
            )
            for i in range(1, 6)
        ]

    def create(self, user, **fields):
        body = {"name": "Sortie", "participants": [user.pk], "mode": "walk", "duration_minutes": 60, "is_loop": True}
        return self.client_for(user).post("/api/outings/", {**body, **START, **fields}, format="json")

    def stop_names(self, response):
        return [stop["invader"]["name"] for stop in response.json()["stops"]]

    def test_plans_nearby_invaders_in_order_within_the_duration(self):
        response = self.create(self.bob, duration_minutes=90)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.stop_names(response), ["PA_11", "PA_12", "PA_13", "PA_14", "PA_15"])
        self.assertLessEqual(response.json()["estimate"]["minutes"], 90)

    def test_a_short_outing_keeps_fewer_invaders(self):
        response = self.create(self.bob, duration_minutes=15)
        self.assertLess(len(self.stop_names(response)), 5)
        self.assertLessEqual(response.json()["estimate"]["minutes"], 15)

    def test_skips_invaders_flashed_by_a_participant_and_destroyed_ones(self):
        Flash.objects.create(user=self.carol, invader=self.line[0], flashed_at=datetime.date(2026, 1, 1))
        Invader.objects.filter(pk=self.line[1].pk).update(status=Status.DESTROYED)
        names = self.stop_names(self.create(self.bob, participants=[self.bob.pk, self.carol.pk]))
        self.assertNotIn("PA_11", names)
        self.assertNotIn("PA_12", names)
        self.assertIn("PA_13", names)

    def test_a_loop_ends_at_the_start(self):
        outing = Outing.objects.get(pk=self.create(self.bob, end_lat=1, end_lng=1).json()["id"])
        self.assertEqual((outing.end_lat, outing.end_lng), (outing.start_lat, outing.start_lng))

    def test_a_one_way_outing_needs_an_end(self):
        self.assertEqual(self.create(self.bob, is_loop=False).status_code, 400)

    def test_stops_can_be_reordered_and_removed(self):
        # One way to the north: the order matters.
        outing_id = self.create(self.bob, is_loop=False, end_lat=48.88, end_lng=2.3522).json()["id"]
        stop_ids = [self.line[2].pk, self.line[0].pk]
        response = self.client_for(self.carol).patch(f"/api/outings/{outing_id}/", {"stop_ids": stop_ids}, format="json")
        self.assertEqual(self.stop_names(response), ["PA_13", "PA_11"])
        optimized = self.client_for(self.bob).post(f"/api/outings/{outing_id}/optimize/")
        self.assertEqual(self.stop_names(optimized), ["PA_11", "PA_13"])

    def test_done_once_every_participant_flashed_it(self):
        outing_id = self.create(self.bob, participants=[self.bob.pk, self.carol.pk]).json()["id"]
        Flash.objects.create(user=self.bob, invader=self.line[0], flashed_at=datetime.date(2026, 1, 1))
        stops = self.client_for(self.bob).get(f"/api/outings/{outing_id}/").json()["stops"]
        self.assertFalse(stops[0]["done"])
        Flash.objects.create(user=self.carol, invader=self.line[0], flashed_at=datetime.date(2026, 1, 1))
        stops = self.client_for(self.bob).get(f"/api/outings/{outing_id}/").json()["stops"]
        self.assertTrue(stops[0]["done"])

    def test_other_teams_cannot_see_or_use_outings(self):
        outing_id = self.create(self.bob).json()["id"]
        eve = self.client_for(self.eve)
        self.assertEqual(eve.get("/api/outings/").json(), [])
        self.assertEqual(eve.get(f"/api/outings/{outing_id}/").status_code, 404)
        # Members, stops and cities of another team are refused.
        self.assertEqual(self.create(self.eve, participants=[self.bob.pk]).status_code, 400)
        response = self.client_for(self.bob).patch(
            f"/api/outings/{outing_id}/", {"stop_ids": [self.rom_1.pk]}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_only_the_author_or_an_admin_can_delete(self):
        outing_id = self.create(self.bob).json()["id"]
        self.assertEqual(self.client_for(self.carol).delete(f"/api/outings/{outing_id}/").status_code, 403)
        self.assertEqual(self.client_for(self.admin).delete(f"/api/outings/{outing_id}/").status_code, 204)


class PlannerTests(InvadersTestCase):
    def test_estimate_adds_detours_and_flash_time(self):
        start, end = (48.8566, 2.3522), (48.8656, 2.3522)  # 1 km north
        result = outings.estimate(start, [], end, "walk")
        self.assertEqual(result["distance_km"], 1.3)
        self.assertEqual(result["minutes"], round(1.3 / 4.5 * 60))
        self.assertEqual(outings.estimate(start, [end], end, "walk")["minutes"], result["minutes"] + 2)
