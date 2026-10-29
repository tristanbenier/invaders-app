from apps.invaders.models import Invader
from apps.invaders.tests.test_security import InvadersTestCase


class PointsFilterTests(InvadersTestCase):
    def test_filters_on_several_point_values(self):
        for name, points in (("PA_2", 20), ("PA_3", 50), ("PA_4", 100)):
            Invader.objects.create(team=self.team_a, name=name, city=self.paris, lat=48.8, lng=2.3, points=points)
        response = self.client_for(self.bob).get("/api/invaders/", {"points": "10,100"})
        self.assertEqual(sorted(invader["name"] for invader in response.json()), ["PA_1", "PA_4"])

    def test_invalid_points_are_refused(self):
        response = self.client_for(self.bob).get("/api/invaders/", {"points": "10,abc"})
        self.assertEqual(response.status_code, 400)
