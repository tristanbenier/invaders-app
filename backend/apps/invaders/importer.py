"""Bulk import of invaders from a JSON file.

Expected format: a list of objects with name, lat, lng, points and optionally
status, address1, address2, zip, comment, city and flashed_by:

- The city is the team city whose prefix matches the name. When there is none,
  a "city" object ({"name", "prefix"?, "country"?}) creates it on the fly, in
  its country (created too if needed, "France" by default).
- "flashed_by" lists the team members who flashed the invader: emails, or
  {"email", "flashed_at"?} objects (date defaults to today). Existing flashes
  are kept as they are.

Rows are matched on name within the team: unknown names are created, known
ones are updated. Other keys are ignored. The import is all-or-nothing.
"""

import json

import datetime

from django.db import transaction
from django.utils import timezone

from . import history
from apps.accounts.models import User

from .models import City, Country, Flash, HistoryAction, Invader
from .naming import parse_name
from .serializers import InvaderSerializer

MAX_FILE_SIZE = 5 * 1024 * 1024
IMPORTED_FIELDS = ["lat", "lng", "points", "status", "address1", "address2", "zip", "comment"]
DEFAULT_COUNTRY = "France"


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


def _plan_city(row, prefix, cities_by_prefix, new_cities):
    """Unsaved city for an unknown prefix, from the row's "city" object; error message otherwise."""
    city = row.get("city")
    if not isinstance(city, dict) or not str(city.get("name") or "").strip():
        return None, f"Aucune ville ne correspond au préfixe {prefix} et la ligne ne décrit pas de ville à créer."
    if city.get("prefix") and str(city["prefix"]).strip().rstrip("_").upper() != prefix:
        return None, f"Le préfixe de la ville ({city['prefix']}) ne correspond pas au nom de l'invader."
    name = str(city["name"]).strip()[:100]
    country = str(city.get("country") or "").strip()[:100] or DEFAULT_COUNTRY
    # Unsaved placeholder, replaced by the real city in commit().
    planned = City(name=name, prefix=prefix)
    planned.country_name = country
    cities_by_prefix[prefix] = new_cities[prefix] = planned
    return planned, None


def _plan_flashes(row, members_by_email, today):
    """[(user, date)] from the row's "flashed_by", or a list of error messages."""
    entries = row.get("flashed_by") or []
    if not isinstance(entries, list):
        return None, ["« flashed_by » doit être une liste."]
    flashes, errors = [], []
    for entry in entries:
        email, flashed_at = (entry, None) if isinstance(entry, str) else (
            (entry.get("email"), entry.get("flashed_at")) if isinstance(entry, dict) else (None, None)
        )
        user = members_by_email.get(str(email or "").strip().lower())
        if user is None:
            errors.append(f"Membre inconnu dans l'équipe : {email}.")
            continue
        try:
            date = datetime.date.fromisoformat(flashed_at) if flashed_at else today
        except (TypeError, ValueError):
            errors.append(f"Date de flash invalide pour {email} : {flashed_at}.")
            continue
        if date > today:
            errors.append(f"La date de flash de {email} est dans le futur.")
            continue
        flashes.append((user, date))
    return (None, errors) if errors else (flashes, [])


def analyze(team, rows):
    """Validate every row and describe what the import would do."""
    existing = {invader.name: invader for invader in Invader.objects.filter(team=team)}
    cities_by_prefix = {city.prefix: city for city in City.objects.filter(team=team)}
    members_by_email = {user.email.lower(): user for user in User.objects.filter(team=team, is_active=True)}
    context = {"team": team, "check_unique": False, "cities_by_prefix": cities_by_prefix}
    today = timezone.localdate()
    seen = set()
    result = {
        "to_create": [],
        "to_update": [],
        "unchanged": [],
        "errors": [],
        "new_cities": {},
        "existing_countries": {name.lower() for name in Country.objects.filter(team=team).values_list("name", flat=True)},
    }

    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            result["errors"].append({"index": index, "name": None, "errors": ["Chaque élément doit être un objet."]})
            continue
        raw_name = str(row.get("name", "")).strip().upper()
        parsed = parse_name(raw_name)
        if parsed and parsed[0] not in cities_by_prefix:
            _, error = _plan_city(row, parsed[0], cities_by_prefix, result["new_cities"])
            if error:
                result["errors"].append({"index": index, "name": raw_name, "errors": {"city": [error]}})
                continue
        flashes, flash_errors = _plan_flashes(row, members_by_email, today)
        if flash_errors:
            result["errors"].append({"index": index, "name": raw_name or None, "errors": {"flashed_by": flash_errors}})
            continue

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
            result["to_create"].append({"index": index, "data": data, "flashes": flashes})
        else:
            changes = _changes(instance, data)
            target = result["to_update"] if changes else result["unchanged"]
            target.append({"index": index, "instance": instance, "data": data, "changes": changes, "flashes": flashes})
    return result


def summarize(result):
    items = result["to_create"] + result["to_update"] + result["unchanged"]
    new_cities = [
        {"name": city.name, "prefix": city.prefix, "country": city.country_name} for city in result["new_cities"].values()
    ]
    return {
        "counts": {
            "to_create": len(result["to_create"]),
            "to_update": len(result["to_update"]),
            "unchanged": len(result["unchanged"]),
            "errors": len(result["errors"]),
            "cities_to_create": len(new_cities),
            "flashes": sum(len(item["flashes"]) for item in items),
        },
        "cities_to_create": new_cities,
        "countries_to_create": sorted({city["country"] for city in new_cities if city["country"].lower() not in result["existing_countries"]}),
        "to_create": [item["data"]["name"] for item in result["to_create"]],
        "to_update": [{"name": item["instance"].name, "changes": item["changes"]} for item in result["to_update"]],
        "unchanged": [item["instance"].name for item in result["unchanged"]],
        "errors": result["errors"],
    }


def _create_cities(team, new_cities):
    """Create the planned cities (and their countries); returns {prefix: City}."""
    countries = {country.name.lower(): country for country in Country.objects.filter(team=team)}
    created = {}
    for prefix, planned in new_cities.items():
        key = planned.country_name.lower()
        if key not in countries:
            countries[key] = Country.objects.create(team=team, name=planned.country_name)
        created[prefix] = City.objects.create(team=team, name=planned.name, prefix=prefix, country=countries[key])
    return created


def _create_flashes(pairs):
    """Bulk-create (user, invader, date) flashes, keeping flashes that already exist."""
    if not pairs:
        return 0
    invader_ids = {invader.pk for _, invader, _ in pairs}
    existing = set(Flash.objects.filter(invader_id__in=invader_ids).values_list("user_id", "invader_id"))
    new = {}
    for member, invader, date in pairs:
        key = (member.pk, invader.pk)
        if key not in existing:
            new.setdefault(key, Flash(user=member, invader=invader, flashed_at=date))
    return len(Flash.objects.bulk_create(new.values()))


@transaction.atomic
def commit(team, user, result, mark_as_flashed):
    cities = _create_cities(team, result["new_cities"])
    flash_pairs = []
    created = []
    for item in result["to_create"]:
        if (planned := item["data"]["city"]).pk is None:
            item["data"]["city"] = cities[planned.prefix]
        invader = Invader.objects.create(team=team, created_by=user, **item["data"])
        history.record(invader, user, HistoryAction.IMPORTED)
        created.append(invader)
        flash_pairs += [(member, invader, date) for member, date in item["flashes"]]
    for item in result["to_update"]:
        invader = item["instance"]
        before = history.snapshot(invader)
        for field, change in item["changes"].items():
            setattr(invader, field, change["new"])
        invader.save()
        history.record(invader, user, HistoryAction.IMPORTED, before)
    for item in result["to_update"] + result["unchanged"]:
        flash_pairs += [(member, item["instance"], date) for member, date in item["flashes"]]

    if mark_as_flashed:
        today = timezone.localdate()
        invaders = created + [item["instance"] for item in result["to_update"] + result["unchanged"]]
        flash_pairs += [(user, invader, today) for invader in invaders]
    # Existing flashes keep their original date.
    flashed = _create_flashes(flash_pairs)
    return {"created": len(created), "updated": len(result["to_update"]), "cities_created": len(cities), "flashed": flashed}
