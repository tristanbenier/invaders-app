"""Shared helpers for the test suites (`manage.py test`)."""

import logging
import shutil
import tempfile
from pathlib import Path

from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.accounts.models import Role, Team, User

PASSWORD = "Str0ng-pass!"


@override_settings(
    # Never share throttle counters with the dev server's file cache.
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
)
class ApiTestCase(TestCase):
    """Two teams: A (admin, bob, carol) and B (eve, admin of her team)."""

    @classmethod
    def setUpTestData(cls):
        cls.team_a = Team.objects.create(name="A")
        cls.team_b = Team.objects.create(name="B")
        cls.admin = cls.make_user("admin", cls.team_a, Role.ADMIN)
        cls.bob = cls.make_user("bob", cls.team_a)
        cls.carol = cls.make_user("carol", cls.team_a)
        cls.eve = cls.make_user("eve", cls.team_b, Role.ADMIN)

    @staticmethod
    def make_user(name, team, role=Role.MEMBER):
        return User.objects.create_user(f"{name}@example.test", PASSWORD, display_name=name.title(), team=team, role=role)

    def setUp(self):
        cache.clear()
        # Refused requests are the point of these tests: keep their warnings out of the output.
        request_logger = logging.getLogger("django.request")
        previous_level = request_logger.level
        request_logger.setLevel(logging.ERROR)
        self.addCleanup(request_logger.setLevel, previous_level)
        # Uploaded images and cached tiles go to a throwaway directory.
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp_dir, ignore_errors=True)
        overrides = override_settings(MEDIA_ROOT=self.tmp_dir / "media", TILE_CACHE_DIR=self.tmp_dir / "tiles")
        overrides.enable()
        self.addCleanup(overrides.disable)

    def client_for(self, user=None):
        client = APIClient()
        if user is not None:
            client.force_authenticate(user)
        return client
