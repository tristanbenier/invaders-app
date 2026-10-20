from .models import InvaderHistory

TRACKED_FIELDS = ["name", "lat", "lng", "points", "status", "image", "address1", "address2", "zip", "comment"]


def snapshot(invader):
    """Comparable values of the tracked fields (image: file name, "" when none)."""
    return {
        "name": invader.name,
        "lat": round(float(invader.lat), 6),
        "lng": round(float(invader.lng), 6),
        "points": invader.points,
        "status": invader.status,
        "image": invader.image.name or "",
        "address1": invader.address1,
        "address2": invader.address2,
        "zip": invader.zip,
        "comment": invader.comment,
    }


def record(invader, user, action, before=None):
    """Store a history entry. Without `before` (a creation) nothing is compared;
    otherwise the entry is only stored when a tracked field actually changed."""
    if before is None:
        return InvaderHistory.objects.create(invader=invader, user=user, action=action)
    after = snapshot(invader)
    changes = {
        field: {"old": before[field], "new": after[field]}
        for field in TRACKED_FIELDS
        if before[field] != after[field]
    }
    if "image" in changes:
        # File names are meaningless to readers: only say whether there is an image.
        changes["image"] = {"old": bool(before["image"]), "new": bool(after["image"])}
    if not changes:
        return None
    return InvaderHistory.objects.create(invader=invader, user=user, action=action, changes=changes)
