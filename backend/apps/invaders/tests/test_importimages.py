import io
import json

from django.core.files.base import ContentFile
from django.core.management import call_command
from PIL import Image

from apps.invaders.models import Invader, InvaderHistory
from apps.invaders.tests.test_security import InvadersTestCase


def png(size, color=(200, 30, 30, 255)):
    buffer = io.BytesIO()
    Image.new("RGBA", size, color).save(buffer, "PNG")
    return buffer.getvalue()


class ImportImagesCommandTests(InvadersTestCase):
    def setUp(self):
        super().setUp()
        self.data = self.tmp_dir / "data"
        (self.data / "images" / "invaders").mkdir(parents=True)
        (self.data / "images" / "cities").mkdir(parents=True)
        self.pa_2 = Invader.objects.create(team=self.team_a, name="PA_2", city=self.paris, lat=48.8, lng=2.3, points=10)
        self.write_file("invaders", "PA_1.abc.png", png((800, 800)))
        self.write_file("invaders", "PA_2.def.png", png((1600, 900), color=(0, 0, 0, 0)))  # Wide, transparent.
        self.write_file("cities", "paris.jpg", png((1000, 500)))
        self.write_json("invaders.json", [
            {"name": "PA_1", "images": ["/upload/images/invaders/PA_1.abc.png", "/upload/images/invaders/other.png"]},
            {"name": "PA_2", "images": ["/upload/images/invaders/PA_2.def.png"]},
            {"name": "PA_3", "images": ["/upload/images/invaders/PA_3.png"]},  # Not in the team: ignored.
        ])
        self.write_json("cities.json", [{"prefix": "PA_", "fileUrl": "/upload/images/cities/paris.jpg"}])

    def write_file(self, folder, name, content):
        (self.data / "images" / folder / name).write_bytes(content)

    def write_json(self, name, rows):
        (self.data / name).write_text(json.dumps(rows), encoding="utf-8")

    def run_command(self, *args):
        out = io.StringIO()
        call_command("importimages", "A", "--data", str(self.data), *args, stdout=out)
        return out.getvalue()

    def image_of(self, obj):
        obj.refresh_from_db()
        with obj.image.open("rb") as file, Image.open(file) as image:
            return image.format, image.size, image.convert("RGB").getpixel((0, 0))

    def test_photos_keep_their_proportions(self):
        self.run_command()
        self.assertEqual(self.image_of(self.pa_1)[:2], ("JPEG", (800, 800)))
        fmt, size, corner = self.image_of(self.pa_2)
        self.assertEqual((fmt, size), ("JPEG", (1200, 675)))  # Shrunk, not cropped.
        self.assertEqual(corner, (255, 255, 255))  # Transparency became white.
        self.assertEqual(self.image_of(self.paris)[1], (1000, 500))

    def test_history_records_the_photo(self):
        self.run_command()
        entry = InvaderHistory.objects.filter(invader=self.pa_1).latest("created_at")
        self.assertEqual(entry.changes, {"image": {"old": False, "new": True}})
        self.assertEqual(entry.user, self.admin)

    def test_existing_photos_are_skipped_unless_overwrite(self):
        self.pa_1.image.save("kept.jpg", ContentFile(png((10, 10))))
        kept = self.pa_1.image.name
        output = self.run_command()
        self.assertIn("1 skipped", output)
        self.pa_1.refresh_from_db()
        self.assertEqual(self.pa_1.image.name, kept)

        self.run_command("--overwrite")
        self.pa_1.refresh_from_db()
        self.assertNotEqual(self.pa_1.image.name, kept)
        self.assertFalse(self.pa_1.image.storage.exists(kept))  # Replaced file removed.

    def test_dry_run_writes_nothing(self):
        output = self.run_command("--dry-run")
        self.assertIn("would import", output)
        self.pa_1.refresh_from_db()
        self.assertFalse(self.pa_1.image)
        self.assertFalse(InvaderHistory.objects.exists())

    def test_missing_file_is_reported(self):
        (self.data / "images" / "invaders" / "PA_2.def.png").unlink()
        output = self.run_command()
        self.assertIn("PA_2: missing file PA_2.def.png", output)
        self.pa_2.refresh_from_db()
        self.assertFalse(self.pa_2.image)
