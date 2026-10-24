import io
import json

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from PIL import Image

from apps.invaders.models import City, Flash, Invader
from apps.invaders.tests.test_security import InvadersTestCase

IMPORT_URL = "/admin/invaders/invader/import/"
PHOTOS_URL = "/admin/invaders/invader/upload-photos/"


def json_file(rows):
    return SimpleUploadedFile("invaders.json", json.dumps(rows).encode(), content_type="application/json")


def image_file(name, size=(400, 300)):
    buffer = io.BytesIO()
    Image.new("RGB", size, (10, 120, 200)).save(buffer, "PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


class AdminImportTestCase(InvadersTestCase):
    def setUp(self):
        super().setUp()
        self.admin.is_staff = self.admin.is_superuser = True
        self.admin.save()
        self.browser = Client()
        self.browser.force_login(self.admin)


class InvaderImportScreenTests(AdminImportTestCase):
    def preview(self, rows, **extra):
        data = {"team": self.team_a.pk, "author": self.admin.pk, "file": json_file(rows), **extra}
        return self.browser.post(IMPORT_URL, data)

    def test_buttons_are_shown_on_the_invader_list(self):
        page = self.browser.get("/admin/invaders/invader/").content.decode()
        self.assertIn(IMPORT_URL, page)
        self.assertIn(PHOTOS_URL, page)

    def test_preview_then_confirm_imports(self):
        rows = [{"name": "LY_1", "lat": 45.7, "lng": 4.8, "points": 10, "city": {"name": "Lyon"}, "flashed_by": ["bob@example.test"]}]
        response = self.preview(rows)
        self.assertContains(response, "Confirmer l'import")
        self.assertContains(response, "Lyon (LY, France)")
        self.assertFalse(Invader.objects.filter(name="LY_1").exists())  # Preview writes nothing.

        token = response.context["token"]
        response = self.browser.post(
            IMPORT_URL, {"step": "confirm", "token": token, "team": self.team_a.pk, "author": self.admin.pk}, follow=True
        )
        self.assertContains(response, "1 créé(s)")
        invader = Invader.objects.get(name="LY_1")
        self.assertEqual(invader.city, City.objects.get(team=self.team_a, prefix="LY"))
        self.assertEqual(invader.created_by, self.admin)
        self.assertTrue(Flash.objects.filter(user=self.bob, invader=invader).exists())

    def test_errors_block_the_confirmation(self):
        response = self.preview([{"name": "Hello", "lat": 1, "lng": 1, "points": 10}])
        self.assertContains(response, "Le nom doit avoir la forme")
        self.assertNotContains(response, "Confirmer l'import")

    def test_author_must_belong_to_the_team(self):
        response = self.browser.post(
            IMPORT_URL, {"team": self.team_a.pk, "author": self.eve.pk, "file": json_file([{"name": "PA_9"}])}
        )
        self.assertEqual(response.context["form"].errors["author"], ["L'auteur doit faire partie de l'équipe choisie."])

    def test_unknown_token_is_refused(self):
        response = self.browser.post(
            IMPORT_URL, {"step": "confirm", "token": "../../etc/passwd", "team": self.team_a.pk, "author": self.admin.pk}
        )
        self.assertRedirects(response, IMPORT_URL, fetch_redirect_response=False)

    def test_screens_require_admin_rights(self):
        member = Client()
        member.force_login(self.bob)  # Not staff.
        self.assertNotEqual(member.get(IMPORT_URL).status_code, 200)
        self.assertNotEqual(member.get(PHOTOS_URL).status_code, 200)


class PhotoUploadScreenTests(AdminImportTestCase):
    def upload(self, *files, **extra):
        data = {"team": self.team_a.pk, "author": self.admin.pk, "photos": list(files), **extra}
        return self.browser.post(PHOTOS_URL, data)

    def test_photos_are_matched_by_file_name(self):
        response = self.upload(image_file("pa_1.5e3ef74d.png"), image_file("PA_404.jpg"), image_file("notes.png"))
        self.assertContains(response, "1 photo(s) ajoutée(s)")
        self.assertContains(response, "aucun invader « PA_404 »")
        self.assertContains(response, "aucun invader « ? »")
        self.pa_1.refresh_from_db()
        with self.pa_1.image.open("rb") as file, Image.open(file) as image:
            self.assertEqual(image.size, (400, 300))  # Proportions kept by default.

    def test_square_option_and_overwrite(self):
        self.upload(image_file("PA_1.png"))
        first = Invader.objects.get(pk=self.pa_1.pk).image.name
        self.assertContains(self.upload(image_file("PA_1.png")), "ignorée(s)")
        self.assertEqual(Invader.objects.get(pk=self.pa_1.pk).image.name, first)

        self.upload(image_file("PA_1.png"), overwrite="on", square="on")
        invader = Invader.objects.get(pk=self.pa_1.pk)
        self.assertNotEqual(invader.image.name, first)
        with invader.image.open("rb") as file, Image.open(file) as image:
            self.assertEqual(image.size, (300, 300))
