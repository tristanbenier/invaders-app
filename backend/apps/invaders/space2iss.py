"""SPACE2ISS, the invader sent to the International Space Station, added to every team.

Called by the 0004 data migration with the historical app registry, so only plain model
operations are used here (no custom methods, no serializers).
"""

from pathlib import Path

from django.core.files.base import ContentFile

from .naming import ISS_INVADER_NAME, SPECIAL_NAMES

PHOTO = Path(__file__).resolve().parent / "assets" / "space2iss.jpg"
COUNTRY_NAME = "Space"
CITY_NAME = "Space"
PREFIX, NUMBER = SPECIAL_NAMES[ISS_INVADER_NAME]
POINTS = 100
COMMENT = "To infinity… and beyond"
# Required by the model only: the map shows the live ISS position instead.
LAT, LNG = 40.457894, -45.726661


def add_to_teams(apps, teams=None):
    """Create the Space country and city, then SPACE2ISS, in each team that lacks it."""
    Team = apps.get_model("accounts", "Team")
    Country = apps.get_model("invaders", "Country")
    City = apps.get_model("invaders", "City")
    Invader = apps.get_model("invaders", "Invader")
    InvaderHistory = apps.get_model("invaders", "InvaderHistory")
    photo = PHOTO.read_bytes()

    for team in teams if teams is not None else Team.objects.all():
        if Invader.objects.filter(team=team, name=ISS_INVADER_NAME).exists():
            continue
        city = City.objects.filter(team=team, prefix=PREFIX).first()
        if city is None:
            country = Country.objects.filter(team=team, name__iexact=COUNTRY_NAME).first()
            if country is None:
                country = Country.objects.create(team=team, name=COUNTRY_NAME)
            city = City.objects.create(team=team, name=CITY_NAME, prefix=PREFIX, country=country)
        # Historical models skip Invader.save(): prefix and number are set by hand.
        invader = Invader.objects.create(
            team=team,
            name=ISS_INVADER_NAME,
            prefix=PREFIX,
            number=NUMBER,
            city=city,
            lat=LAT,
            lng=LNG,
            points=POINTS,
            status="ok",
            comment=COMMENT,
        )
        invader.image.save("space2iss.jpg", ContentFile(photo))
        InvaderHistory.objects.create(invader=invader, user=None, action="created", changes={})
