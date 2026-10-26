from django.test import Client
from rest_framework.test import APIClient

from apps.accounts.models import Invitation, Role, User
from apps.accounts.testing import PASSWORD, ApiTestCase


class ProfileTests(ApiTestCase):
    def test_only_preferences_are_writable(self):
        self.client_for(self.bob).patch(
            "/api/auth/me/",
            {"role": "admin", "team": self.team_b.pk, "email": "x@example.test", "is_superuser": True, "map_theme": "dark"},
            format="json",
        )
        self.bob.refresh_from_db()
        self.assertEqual(self.bob.role, Role.MEMBER)
        self.assertEqual(self.bob.team, self.team_a)
        self.assertEqual(self.bob.email, "bob@example.test")
        self.assertFalse(self.bob.is_superuser)
        self.assertEqual(self.bob.map_theme, "dark")

    def test_anonymous_is_refused(self):
        anonymous = APIClient()
        for url in ["/api/auth/me/", "/api/team/", "/api/invitations/"]:
            with self.subTest(url=url):
                self.assertEqual(anonymous.get(url).status_code, 403)


class TeamTests(ApiTestCase):
    def test_team_page_lists_own_members_only(self):
        members = self.client_for(self.eve).get("/api/team/").json()["members"]
        self.assertEqual({member["display_name"] for member in members}, {"Eve"})

    def test_member_cannot_remove_members(self):
        response = self.client_for(self.bob).delete(f"/api/team/members/{self.carol.pk}/")
        self.assertEqual(response.status_code, 403)
        self.assertTrue(User.objects.get(pk=self.carol.pk).is_active)

    def test_admin_cannot_remove_other_team_member(self):
        response = self.client_for(self.admin).delete(f"/api/team/members/{self.eve.pk}/")
        self.assertEqual(response.status_code, 404)

    def test_removed_member_loses_session_and_login(self):
        browser = Client()
        browser.login(email="carol@example.test", password=PASSWORD)
        self.assertEqual(browser.get("/api/auth/me/").status_code, 200)

        self.client_for(self.admin).delete(f"/api/team/members/{self.carol.pk}/")

        self.assertEqual(browser.get("/api/auth/me/").status_code, 403)
        response = APIClient().post("/api/auth/login/", {"email": "carol@example.test", "password": PASSWORD}, format="json")
        self.assertIn(response.status_code, (400, 403))


class InvitationTests(ApiTestCase):
    def test_member_cannot_create_admin_invitation(self):
        response = self.client_for(self.bob).post("/api/invitations/", {"role": "admin", "email": ""}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Invitation.objects.get(pk=response.json()["id"]).role, Role.MEMBER)

    def test_member_cannot_revoke_someone_elses_invitation(self):
        invitation = Invitation.objects.create(team=self.team_a, invited_by=self.carol)
        response = self.client_for(self.bob).delete(f"/api/invitations/{invitation.pk}/")
        self.assertEqual(response.status_code, 403)

    def test_other_team_cannot_revoke_invitation(self):
        invitation = Invitation.objects.create(team=self.team_a, invited_by=self.carol)
        response = self.client_for(self.eve).delete(f"/api/invitations/{invitation.pk}/")
        self.assertEqual(response.status_code, 404)

    def test_invitation_cannot_be_used_twice(self):
        invitation = Invitation.objects.create(team=self.team_a, invited_by=self.admin)
        payload = {"token": invitation.token, "display_name": "Dan", "password": PASSWORD}
        first = APIClient().post("/api/auth/accept-invitation/", {**payload, "email": "dan@example.test"}, format="json")
        second = APIClient().post("/api/auth/accept-invitation/", {**payload, "email": "dan2@example.test"}, format="json")
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 400)
        self.assertFalse(User.objects.filter(email="dan2@example.test").exists())


class CsrfAndLoginTests(ApiTestCase):
    def test_session_write_without_csrf_token_is_refused(self):
        client = APIClient(enforce_csrf_checks=True)
        client.login(email="bob@example.test", password=PASSWORD)
        response = client.post("/api/invitations/", {}, format="json")
        self.assertEqual(response.status_code, 403)

    def test_login_brute_force_is_throttled(self):
        codes = [
            APIClient().post("/api/auth/login/", {"email": "bob@example.test", "password": "wrong"}, format="json").status_code
            for _ in range(12)
        ]
        self.assertIn(429, codes)

    def test_admin_login_brute_force_is_throttled(self):
        codes = [Client().post("/admin/login/", {"username": "admin@example.test", "password": "wrong"}).status_code for _ in range(12)]
        self.assertEqual(codes[:10], [200] * 10)
        self.assertEqual(codes[10:], [429, 429])


class HostingMiddlewareTests(ApiTestCase):
    def test_client_ip_header_gives_each_visitor_its_own_throttle(self):
        def login(ip):
            return Client(HTTP_X_REAL_IP=ip).post("/admin/login/", {"username": "admin@example.test", "password": "wrong"}).status_code

        with self.settings(CLIENT_IP_HEADER="X-Real-IP"):
            codes = [login("203.0.113.1") for _ in range(11)]
            self.assertEqual(codes[-1], 429)
            self.assertEqual(login("203.0.113.2"), 200)

    def test_oversized_body_is_refused(self):
        with self.settings(MAX_REQUEST_BODY_MB=1):
            response = Client().post("/api/auth/login/", data=b"x" * (1024 * 1024 + 1), content_type="application/json")
        self.assertEqual(response.status_code, 413)

    def test_security_headers_skip_the_admin(self):
        with self.settings(SECURITY_HEADERS=True):
            page = Client().get("/")
            admin = Client().get("/admin/login/")
        self.assertIn("script-src 'self'", page["Content-Security-Policy"])
        self.assertIn("geolocation=(self)", page["Permissions-Policy"])
        self.assertNotIn("Content-Security-Policy", admin)
