"""Import invader and city photos from the previous version's export.

Usage (from backend/):
    .venv/bin/python manage.py importimages "Mon équipe" --data ../data

Expects in --data:
    invaders.json   rows with "name" and "images" (paths such as "/upload/images/invaders/PA_1.abc.png")
    cities.json     rows with "prefix" ("PA_") and "fileUrl" (optional)
    images/invaders/ and images/cities/   the files themselves

Photos keep their proportions (no square crop) and are re-encoded as JPEG
like app uploads. Invaders and cities that already have a photo are skipped
unless --overwrite.
"""

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import Role, Team, User
from apps.invaders.models import City, Invader
from apps.invaders.photos import InvalidImage, attach_photo


class Command(BaseCommand):
    help = "Import invader and city photos from the previous version's export (data/ folder)."

    def add_arguments(self, parser):
        parser.add_argument("team", help="Team name")
        parser.add_argument("--data", default="../data", help="Export folder (default: ../data)")
        parser.add_argument("--user", help="Email recorded as author in the history (default: first team admin)")
        parser.add_argument("--overwrite", action="store_true", help="Replace photos that already exist")
        parser.add_argument("--dry-run", action="store_true", help="Report what would be imported, write nothing")
        parser.add_argument("--skip-cities", action="store_true", help="Only import invader photos")

    def handle(self, *args, team, data, user, overwrite, dry_run, skip_cities, **options):
        try:
            self.team = Team.objects.get(name=team)
        except Team.DoesNotExist:
            raise CommandError(f"Unknown team: {team}")
        self.data = Path(data).resolve()
        self.user = self._author(user)
        self.overwrite, self.dry_run = overwrite, dry_run

        self._import_invaders()
        if not skip_cities:
            self._import_cities()

    def _author(self, email):
        members = User.objects.filter(team=self.team, is_active=True)
        author = members.filter(email__iexact=email).first() if email else members.filter(role=Role.ADMIN).first()
        if author is None:
            raise CommandError(f"No such team member: {email}" if email else "The team has no admin")
        return author

    def _load(self, filename):
        path = self.data / filename
        if not path.is_file():
            raise CommandError(f"Missing file: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def _source(self, folder, url):
        # Only the file name is used: the export's paths point to the old server.
        return self.data / "images" / folder / Path(url).name

    def _attach(self, obj, source):
        """Save the photo on `obj`, keeping its proportions; returns an error message or None."""
        if not source.is_file():
            return f"missing file {source.name}"
        if self.dry_run:
            return None
        try:
            with source.open("rb") as file:
                attach_photo(obj, file, author=self.user)
        except InvalidImage as exc:
            return f"{source.name}: {exc}"
        return None

    def _report(self, label, imported, skipped, problems):
        verb = "would import" if self.dry_run else "imported"
        self.stdout.write(self.style.SUCCESS(f"{label}: {imported} {verb}, {skipped} skipped (already have a photo)."))
        for problem in problems:
            self.stdout.write(self.style.WARNING(f"  {problem}"))

    def _import_invaders(self):
        invaders = {invader.name: invader for invader in Invader.objects.filter(team=self.team)}
        imported = skipped = 0
        problems = []
        for index, row in enumerate(self._load("invaders.json"), start=1):
            images = row.get("images") or []
            invader = invaders.get(str(row.get("name", "")).strip().upper())
            if not images or invader is None:
                continue
            if invader.image and not self.overwrite:
                skipped += 1
                continue
            # The export may list several photos: the first one is the main one.
            error = self._attach(invader, self._source("invaders", images[0]))
            if error:
                problems.append(f"{invader.name}: {error}")
            else:
                imported += 1
            if index % 200 == 0:
                self.stdout.write(f"  … {index} rows read")
        self._report("Invader photos", imported, skipped, problems)

    def _import_cities(self):
        cities = {city.prefix: city for city in City.objects.filter(team=self.team)}
        imported = skipped = 0
        problems = []
        for row in self._load("cities.json"):
            city = cities.get(str(row.get("prefix", "")).strip().rstrip("_").upper())
            if city is None or not row.get("fileUrl"):
                continue
            if city.image and not self.overwrite:
                skipped += 1
                continue
            error = self._attach(city, self._source("cities", row["fileUrl"]))
            if error:
                problems.append(f"{city.name}: {error}")
            else:
                imported += 1
        self._report("City photos", imported, skipped, problems)
