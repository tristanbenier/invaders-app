import time

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Delete cached map tiles not refreshed for a while (run e.g. weekly from cron)."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=30, help="Maximum age of a cached tile (default: 30)")

    def handle(self, *args, days, **options):
        root = settings.TILE_CACHE_DIR
        if not root.exists():
            self.stdout.write("No tile cache.")
            return
        limit = time.time() - days * 24 * 60 * 60
        removed = 0
        for path in root.rglob("*.png"):
            if path.stat().st_mtime < limit:
                path.unlink()
                removed += 1
        # Remove the directories left empty, deepest first.
        for directory in sorted((p for p in root.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
            if not any(directory.iterdir()):
                directory.rmdir()
        self.stdout.write(self.style.SUCCESS(f"{removed} cached tile(s) removed."))
