from django.db.models import Count, IntegerField, Q, Sum, Value
from django.db.models.functions import Coalesce
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User

from .models import City, Flash, Invader, Status


class MyStatsView(APIView):
    """Score, progression over time and completion per city for the current user."""

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

        return Response(
            {
                "points": cumulative_points,
                "flashes": cumulative_flashes,
                "cities": sum(1 for row in by_city if row["flashed"]),
                "team_invaders": Invader.objects.filter(team=user.team).count(),
                "timeline": timeline,
                "by_city": by_city,
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
            .order_by("-points", "-flash_count", "display_name")
        )
        return Response(
            {
                "invaders": Invader.objects.filter(team=team).count(),
                "ranking": [
                    {
                        "user": {"id": member.id, "display_name": member.display_name},
                        "points": member.points,
                        "flashes": member.flash_count,
                    }
                    for member in members
                ],
            }
        )
