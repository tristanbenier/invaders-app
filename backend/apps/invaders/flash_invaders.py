"""Members' own flashes, read from the (unofficial) API of the Flash Invaders app.

The app pushes nothing: the SPA asks for a sync when it opens, then every minute while visible.
Each member stores their own app UID (it identifies their account: never sent back to the
browser, never logged, never put in an error message). Only that member's gallery is read.

To keep the load low, the small account summary (flash count) is checked first and the
gallery (about 200 KB) is only fetched when that count changed, on a full sync, or at least
once an hour (to pick up invaders the team added to its map since).
"""

import json
from datetime import datetime, timedelta
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.utils import timezone

from . import history
from .models import Flash, HistoryAction, Invader, Status

TIMEOUT_SECONDS = 10
COUNT_CACHE_SECONDS = 3600
# The account summary (score, flash count) shown on the stats page; refreshed by every sync.
ACCOUNT_CACHE_SECONDS = 60
# A flash this recent proves the invader is intact; older ones say nothing about today.
INTACT_PROOF_DAYS = 7


class FlashInvadersError(Exception):
    """Upstream unreachable or unexpected answer (the message never contains the UID)."""


def _get(endpoint, uid):
    url = f"{settings.FLASH_INVADERS_API_URL.rstrip('/')}/{endpoint}?{urlencode({'uid': uid})}"
    request = Request(url, headers={"User-Agent": settings.GEOCODER_USER_AGENT})
    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            data = json.load(response)
    except (URLError, TimeoutError, ValueError):
        # Exceptions may quote the URL, hence the UID: raise a clean one instead.
        raise FlashInvadersError(f"Flash Invaders API unavailable ({endpoint})") from None
    if not isinstance(data, dict) or data.get("code") != 0:
        raise FlashInvadersError(f"Flash Invaders API refused the request ({endpoint})")
    return data


def check_uid(uid):
    """True when the UID belongs to an existing Flash Invaders account."""
    try:
        _get("account", uid)
    except FlashInvadersError:
        return False
    return True


def _account(user):
    account = _get("account", user.flash_invaders_uid)
    cache.set(f"flash_invaders:account:{user.pk}", account, ACCOUNT_CACHE_SECONDS)
    return account


def score(user):
    """The member's score in the app (it counts every flash, even off the team map), or None."""
    if not user.flash_invaders_uid:
        return None
    account = cache.get(f"flash_invaders:account:{user.pk}")
    if account is None:
        try:
            account = _account(user)
        except FlashInvadersError:
            return None
    value = account.get("score")
    return value if isinstance(value, int) else None


def _flash_date(value):
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except ValueError:
        return timezone.localdate()


def sync(user, full=False):
    """Flash for `user` every team invader flashed in the app, with the app's flash date.

    Returns the names of the newly flashed invaders and the number of flashes whose date was
    corrected. A new flash less than a week old sets the invader back to intact. Flashes are never removed: one cancelled here comes back while the app has it.
    """
    uid = user.flash_invaders_uid
    count_key = f"flash_invaders:count:{user.pk}"
    count = _account(user).get("si_found")
    if not full and count is not None and cache.get(count_key) == count:
        return [], 0

    gallery = _get("gallery", uid).get("invaders")
    if not isinstance(gallery, dict):
        raise FlashInvadersError("Unexpected Flash Invaders gallery")
    flashed = {
        str(entry.get("name") or name).strip().upper(): _flash_date(entry.get("date_flash"))
        for name, entry in gallery.items()
        if isinstance(entry, dict)
    }

    # Existing flashes take the app's date (the date picked here was often just "today").
    stale = [
        flash
        for flash in Flash.objects.filter(user=user, invader__name__in=flashed).select_related("invader")
        if flash.flashed_at != flashed[flash.invader.name]
    ]
    for flash in stale:
        flash.flashed_at = flashed[flash.invader.name]
    Flash.objects.bulk_update(stale, ["flashed_at"])

    already = Flash.objects.filter(user=user).values_list("invader_id", flat=True)
    # Invaders the team has not mapped yet are skipped (the API gives no position).
    missing = Invader.objects.filter(team=user.team, name__in=flashed).exclude(pk__in=already)
    created = []
    proof_since = timezone.localdate() - timedelta(days=INTACT_PROOF_DAYS)
    for invader in missing:
        flashed_at = flashed[invader.name]
        try:
            with transaction.atomic():
                Flash.objects.create(user=user, invader=invader, flashed_at=flashed_at)
                if invader.status != Status.OK and flashed_at >= proof_since:
                    before = history.snapshot(invader)
                    invader.status = Status.OK
                    invader.save(update_fields=["status", "updated_at"])
                    history.record(invader, user, HistoryAction.UPDATED, before)
        except IntegrityError:
            # Flashed meanwhile (another tab or the button): nothing to do.
            continue
        created.append(invader.name)

    cache.set(count_key, count, COUNT_CACHE_SECONDS)
    return sorted(created), len(stale)
