from datetime import timedelta

from django.utils import timezone

from apps.accounts.models import PasswordReset
from apps.accounts.testing import PASSWORD, ApiTestCase

NEW_PASSWORD = "An0ther-strong-pass!"


class PasswordResetTests(ApiTestCase):
    def create_link(self, member, by=None):
        response = self.client_for(by or self.admin).post(f"/api/team/members/{member.pk}/password-reset/")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response["Cache-Control"], "no-store")
        return response.json()["url"].rsplit("/", 1)[1]

    def reset(self, token, password=NEW_PASSWORD):
        return self.client_for().post("/api/auth/reset-password/", {"token": token, "password": password}, format="json")

    def test_admin_link_sets_a_new_password_once(self):
        token = self.create_link(self.bob)
        self.assertEqual(self.client_for().get(f"/api/auth/password-resets/{token}/").json()["display_name"], "Bob")

        response = self.reset(token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["email"], "bob@example.test")
        self.bob.refresh_from_db()
        self.assertTrue(self.bob.check_password(NEW_PASSWORD))
        self.assertFalse(self.bob.check_password(PASSWORD))
        # Single use.
        self.assertEqual(self.reset(token, "Yet-an0ther-pass!").status_code, 400)
        self.assertEqual(self.client_for().get(f"/api/auth/password-resets/{token}/").status_code, 400)

    def test_only_the_token_hash_is_stored(self):
        token = self.create_link(self.bob)
        self.assertFalse(PasswordReset.objects.filter(token_hash=token).exists())
        self.assertIsNotNone(PasswordReset.find(token))

    def test_member_cannot_create_a_link(self):
        response = self.client_for(self.bob).post(f"/api/team/members/{self.carol.pk}/password-reset/")
        self.assertEqual(response.status_code, 403)
        self.assertFalse(PasswordReset.objects.exists())

    def test_admin_cannot_create_a_link_for_another_team(self):
        response = self.client_for(self.admin).post(f"/api/team/members/{self.eve.pk}/password-reset/")
        self.assertEqual(response.status_code, 404)
        self.assertFalse(PasswordReset.objects.exists())

    def test_new_link_cancels_the_previous_one(self):
        first = self.create_link(self.bob)
        second = self.create_link(self.bob)
        self.assertEqual(self.reset(first).status_code, 400)
        self.assertEqual(self.reset(second).status_code, 200)

    def test_expired_link_is_refused(self):
        token = self.create_link(self.bob)
        PasswordReset.objects.update(expires_at=timezone.now() - timedelta(minutes=1))
        self.assertEqual(self.reset(token).status_code, 400)

    def test_removed_member_cannot_use_a_link(self):
        token = self.create_link(self.bob)
        self.bob.is_active = False
        self.bob.save(update_fields=["is_active"])
        self.assertEqual(self.reset(token).status_code, 400)

    def test_weak_password_is_refused(self):
        token = self.create_link(self.bob)
        response = self.reset(token, "123")
        self.assertEqual(response.status_code, 400)
        self.assertIn("password", response.json())
        # The link stays usable.
        self.assertEqual(self.reset(token).status_code, 200)

    def test_unknown_token_is_refused(self):
        self.assertEqual(self.reset("not-a-token").status_code, 400)
        self.assertEqual(self.client_for().get("/api/auth/password-resets/not-a-token/").status_code, 400)
