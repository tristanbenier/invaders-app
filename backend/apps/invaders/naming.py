import re

NAME_PATTERN = re.compile(r"^(?P<prefix>[A-Z]+)_(?P<number>\d+)$")
PREFIX_PATTERN = re.compile(r"^[A-Z]+$")
# Loose user input such as "pa 123", "pa123", "PA-123" or "pa_0123".
SEARCH_PATTERN = re.compile(r"^(?P<prefix>[A-Z]+)[\s_-]*(?P<number>\d+)$")


def parse_name(name):
    """Return (prefix, number) for a name like "PA_123", or None if invalid."""
    match = NAME_PATTERN.match(name)
    if match is None:
        return None
    return match["prefix"], int(match["number"])


def search_terms(text):
    """Normalize a search: (text to look for in names, (prefix, number) or None).

    "pa 123" and "pa123" become "PA_123", which also matches PA_1234; the
    (prefix, number) pair matches regardless of leading zeros (NA_0001 for "na 1").
    """
    text = text.strip().upper()
    match = SEARCH_PATTERN.match(text)
    if match is None:
        return text, None
    return f"{match['prefix']}_{match['number']}", (match["prefix"], int(match["number"]))
