"""Bulk import of invaders from a JSON file.

Expected format: a list of objects with name, lat, lng, points and optionally
status, address1, address2, zip and comment. The city is found from the name prefix (any "city" key is ignored), so
cities must exist beforehand. Rows are matched on name within the team: unknown
names are created, known ones are updated. The import is all-or-nothing.
"""

import json

from django.db import transaction
from django.utils import timezone

from . import history
from .models import City, Flash, HistoryAction, Invader
from .serializers import InvaderSerializer

MAX_FILE_SIZE = 5 * 1024 * 1024
IMPORTED_FIELDS = ["lat", "lng", "points", "status", "address1", "address2", "zip", "comment"]


class ImportFileError(Exception):
    pass


def read_rows(uploaded_file):
    if uploaded_file.size > MAX_FILE_SIZE:
        raise ImportFileError("Le fichier dépasse la taille maximale de 5 Mo.")
    try:
        rows = json.loads(uploaded_file.read().decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ImportFileError(f"Le fichier n'est pas un JSON valide : {exc}.")
    return validate_rows_shape(rows)


def validate_rows_shape(rows):
    if not isinstance(rows, list):
        raise ImportFileError("Le JSON doit être une liste d'invaders.")
    if not rows:
        raise ImportFileError("Le fichier ne contient aucun invader.")
    return rows


def _changes(invader, data):
    changes = {}
    for field in IMPORTED_FIELDS:
        if field not in data:
            continue
        old, new = getattr(invader, field), data[field]
        if field in ("lat", "lng"):
            old = float(old)
        if old != new:
            changes[field] = {"old": old, "new": new}
    return changes


def analyze(team, rows):
    """Validate every row and describe what the import would do."""
    existing = {invader.name: invader for invader in Invader.objects.filter(team=team)}
    cities_by_prefix = {city.prefix: city for city in City.objects.filter(team=team)}
    context = {"team": team, "check_unique": False, "cities_by_prefix": cities_by_prefix}
    seen = set()
    result = {"to_create": [], "to_update": [], "unchanged": [], "errors": []}

    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            result["errors"].append({"index": index, "name": None, "errors": ["Chaque élément doit être un objet."]})
            continue
        raw_name = str(row.get("name", "")).strip().upper()
        instance = existing.get(raw_name)
        serializer = InvaderSerializer(instance, data=row, context=context)
        if not serializer.is_valid():
            result["errors"].append({"index": index, "name": raw_name or None, "errors": serializer.errors})
            continue
        data = serializer.validated_data
        if data["name"] in seen:
            result["errors"].append(
                {"index": index, "name": data["name"], "errors": ["Ce nom apparaît plusieurs fois dans le fichier."]}
            )
            continue
        seen.add(data["name"])

        if instance is None:
            result["to_create"].append({"index": index, "data": data})
        else:
            changes = _changes(instance, data)
            target = result["to_update"] if changes else result["unchanged"]
            target.append({"index": index, "instance": instance, "data": data, "changes": changes})
    return result


def summarize(result):
    return {
        "counts": {key: len(items) for key, items in result.items()},
        "to_create": [item["data"]["name"] for item in result["to_create"]],
        "to_update": [{"name": item["instance"].name, "changes": item["changes"]} for item in result["to_update"]],
        "unchanged": [item["instance"].name for item in result["unchanged"]],
        "errors": result["errors"],
    }


@transaction.atomic
def commit(team, user, result, mark_as_flashed):
    created = []
    for item in result["to_create"]:
        invader = Invader.objects.create(team=team, created_by=user, **item["data"])
        history.record(invader, user, HistoryAction.IMPORTED)
        created.append(invader)
    for item in result["to_update"]:
        invader = item["instance"]
        before = history.snapshot(invader)
        for field, change in item["changes"].items():
            setattr(invader, field, change["new"])
        invader.save()
        history.record(invader, user, HistoryAction.IMPORTED, before)

    flashed = 0
    if mark_as_flashed:
        invaders = created + [item["instance"] for item in result["to_update"] + result["unchanged"]]
        # Existing flashes keep their original date.
        already_flashed = set(
            Flash.objects.filter(user=user, invader__in=invaders).values_list("invader_id", flat=True)
        )
        today = timezone.localdate()
        new_flashes = Flash.objects.bulk_create(
            [Flash(user=user, invader=invader, flashed_at=today) for invader in invaders if invader.pk not in already_flashed]
        )
        flashed = len(new_flashes)
    return {"created": len(created), "updated": len(result["to_update"]), "flashed": flashed}
