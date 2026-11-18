from concurrent.futures import ThreadPoolExecutor

from django.db.models import Count, IntegerField, Q, Sum, Value
from django.db.models.functions import Coalesce
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User

from . import flash_invaders
from .models import City, Flash, Invader, Status


class MyStatsView(APIView):
    """Score, progression over time and completion per city and per point value for the current user."""

    def get(self, request):
        user = request.user
        flashes = Flash.objects.filter(user=user, invader__team=user.team)

        timeline = []
        cumulative_points = cumulative_flashes = 0
        per_day = (
            flashes.values("flashed_at")
            .annotate(points=Sum("invader__points"), flashes=Count("pk"))
            .order_by("flashed_at")
        )
        for day in per_day:
            cumulative_points += day["points"]
            cumulative_flashes += day["flashes"]
            timeline.append(
                {
                    "date": day["flashed_at"],
                    "points": day["points"],
                    "flashes": day["flashes"],
                    "cumulative_points": cumulative_points,
                    "cumulative_flashes": cumulative_flashes,
                }
            )

        mine = Q(invaders__flashes__user=user)
        # Destroyed invaders only count when already flashed: the others can no longer be flashed.
        cities = (
            City.objects.filter(team=user.team)
            .select_related("country")
            .annotate(
                total=Count("invaders", filter=~Q(invaders__status=Status.DESTROYED) | mine, distinct=True),
                flashed=Count("invaders", filter=mine, distinct=True),
            )
            .filter(total__gt=0)
        )
        by_city = sorted(
            (
                {
                    "city": {"id": city.id, "name": city.name, "prefix": city.prefix},
                    "country": city.country.name,
                    "total": city.total,
                    "flashed": city.flashed,
                }
                for city in cities
            ),
            # Most flashed invaders first; ties by completion rate, then name.
            key=lambda row: (-row["flashed"], -row["flashed"] / row["total"], row["city"]["name"]),
        )

        mine = Q(flashes__user=user)
        by_points = list(
            Invader.objects.filter(team=user.team)
            .values("points")
            .annotate(
                total=Count("pk", filter=~Q(status=Status.DESTROYED) | mine, distinct=True),
                flashed=Count("pk", filter=mine, distinct=True),
            )
            .filter(total__gt=0)
            .order_by("points")
        )

        # A synced member gets the app's score: the team map may lack some of their invaders.
        app_score = flash_invaders.score(user)

        return Response(
            {
                "points": cumulative_points if app_score is None else app_score,
                "points_from_app": app_score is not None,
                "flashes": cumulative_flashes,
                "cities": sum(1 for row in by_city if row["flashed"]),
                "team_invaders": Invader.objects.filter(team=user.team).count(),
                "timeline": timeline,
                "by_city": by_city,
                "by_points": by_points,
            }
        )


class TeamStatsView(APIView):
    """Ranking of the active team members by score."""

    def get(self, request):
        team = request.user.team
        team_flashes = Q(flashes__invader__team=team)
        members = (
            User.objects.filter(team=team, is_active=True)
            .annotate(
                points=Coalesce(Sum("flashes__invader__points", filter=team_flashes), Value(0), output_field=IntegerField()),
                flash_count=Count("flashes", filter=team_flashes),
            )
        )
        # Synced members get their Flash Invaders score (cached a minute, fetched in parallel);
        # the others, or when the app does not answer, the sum of their flashes here.
        synced = [member for member in members if member.flash_invaders_uid]
        with ThreadPoolExecutor(max_workers=4) as pool:
            app_scores = dict(zip((member.pk for member in synced), pool.map(flash_invaders.score, synced)))
        ranking = []
        for member in members:
            app_score = app_scores.get(member.pk)
            ranking.append(
                {
                    "user": {"id": member.id, "display_name": member.display_name},
                    "points": member.points if app_score is None else app_score,
                    "points_from_app": app_score is not None,
                    "flashes": member.flash_count,
                }
            )
        ranking.sort(key=lambda row: (-row["points"], -row["flashes"], row["user"]["display_name"]))
        return Response({"invaders": Invader.objects.filter(team=team).count(), "ranking": ranking})
