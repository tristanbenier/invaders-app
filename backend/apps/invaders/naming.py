import re

NAME_PATTERN = re.compile(r"^(?P<prefix>[A-Z]+)_(?P<number>\d+)$")
PREFIX_PATTERN = re.compile(r"^[A-Z]+$")


def parse_name(name):
    """Return (prefix, number) for a name like "PA_123", or None if invalid."""
    match = NAME_PATTERN.match(name)
    if match is None:
        return None
    return match["prefix"], int(match["number"])
