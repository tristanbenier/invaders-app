from django.conf import settings
from django.core.management.base import BaseCommand

from apps.invaders.tiles import prune


class Command(BaseCommand):
    help = "Delete cached map tiles not refreshed for a while (the app also does it once a day)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days", type=int, default=None, help="Maximum age of a cached tile (default: TILE_CACHE_MAX_DAYS)"
        )

    def handle(self, *args, days, **options):
        days = settings.TILE_CACHE_MAX_DAYS if days is None else days
        removed = prune(days)
        self.stdout.write(self.style.SUCCESS(f"{removed} cached tile(s) older than {days} day(s) removed."))
