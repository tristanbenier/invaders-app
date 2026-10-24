"""Attach photos to invaders and cities outside the API (admin upload, export import)."""

from pathlib import Path

from django.db import transaction

from . import history
from .images import InvalidImage, normalize_image
from .models import HistoryAction, Invader
from .naming import parse_name


def invader_name_from_filename(filename):
    """ "PA_223.5e3ef74def8f1.png" or "pa_223.jpg" -> "PA_223"; None when it is not an invader name."""
    stem = Path(filename).name.split(".", 1)[0].strip().upper()
    return stem if parse_name(stem) else None


def attach_photo(obj, file, *, author=None, square=False):
    """Normalize `file` and save it as the photo of `obj` (Invader or City), replacing any previous one.

    Invader changes are recorded in the history under `author`. Raises InvalidImage.
    """
    content = normalize_image(file, square=square)
    is_invader = isinstance(obj, Invader)
    before = history.snapshot(obj) if is_invader else None
    old = obj.image.name
    with transaction.atomic():
        obj.image.save(content.name, content, save=False)
        obj.save(update_fields=["image", "updated_at"] if is_invader else ["image"])
        if is_invader:
            history.record(obj, author, HistoryAction.IMPORTED, before)
    if old and old != obj.image.name:
        obj.image.storage.delete(old)


__all__ = ["InvalidImage", "attach_photo", "invader_name_from_filename"]
