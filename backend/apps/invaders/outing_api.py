"""Outings API: shared with the whole team, planned by outings.py."""

from django.db import transaction
from django.db.models import Count, IntegerField, OuterRef, Prefetch, Subquery, Value
from django.db.models.functions import Coalesce
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.accounts.models import User

from . import outings
from .models import City, Flash, Invader, Outing, OutingStop


class MemberField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        return User.objects.filter(team=self.context["request"].user.team, is_active=True)


class CityField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        return City.objects.filter(team=self.context["request"].user.team)


class InvaderField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        return Invader.objects.filter(team=self.context["request"].user.team)


def _member(user):
    return {"id": user.pk, "display_name": user.display_name} if user else None


class OutingSerializer(serializers.ModelSerializer):
    participants = MemberField(many=True)
    city = CityField(allow_null=True, required=False)
    # Write: the invaders in visiting order (edit, reorder, remove, add). Read: see `stops`.
    stop_ids = InvaderField(many=True, write_only=True, required=False)
    created_by = serializers.SerializerMethodField()
    participant_names = serializers.SerializerMethodField()
    stops = serializers.SerializerMethodField()
    estimate = serializers.SerializerMethodField()

    class Meta:
        model = Outing
        fields = [
            "id",
            "name",
            "created_by",
            "participants",
            "participant_names",
            "city",
            "mode",
            "duration_minutes",
            "start_lat",
            "start_lng",
            "start_label",
            "is_loop",
            "end_lat",
            "end_lng",
            "end_label",
            "stops",
            "stop_ids",
            "estimate",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {"end_lat": {"required": False}, "end_lng": {"required": False}}

    def validate(self, attrs):
        is_loop = attrs.get("is_loop", self.instance.is_loop if self.instance else False)
        if is_loop:
            attrs["end_lat"] = attrs.get("start_lat", self.instance.start_lat if self.instance else None)
            attrs["end_lng"] = attrs.get("start_lng", self.instance.start_lng if self.instance else None)
            attrs["end_label"] = attrs.get("start_label", self.instance.start_label if self.instance else "")
        elif not self.instance and ("end_lat" not in attrs or "end_lng" not in attrs):
            raise serializers.ValidationError({"end_lat": "Choisissez un point d'arrivée, ou faites une boucle."})
        if "participants" in attrs and not attrs["participants"]:
            raise serializers.ValidationError({"participants": "Choisissez au moins un participant."})
        return attrs

    def get_created_by(self, outing):
        return _member(outing.created_by)

    def get_participant_names(self, outing):
        return [_member(user) for user in outing.participants.all()]

    def _stops(self, outing):
        return list(outing.stops.all())

    def get_stops(self, outing):
        participant_count = len(outing.participants.all())
        return [
            {
                "position": stop.position,
                "invader": {
                    "id": stop.invader.id,
                    "name": stop.invader.name,
                    "lat": stop.invader.lat,
                    "lng": stop.invader.lng,
                    "points": stop.invader.points,
                    "status": stop.invader.status,
                },
                # Every participant flashed it (during or since the outing).
                "done": participant_count > 0 and stop.participant_flashes >= participant_count,
            }
            for stop in self._stops(outing)
        ]

    def get_estimate(self, outing):
        points = [(float(stop.invader.lat), float(stop.invader.lng)) for stop in self._stops(outing)]
        start = (float(outing.start_lat), float(outing.start_lng))
        end = (float(outing.end_lat), float(outing.end_lng))
        return outings.estimate(start, points, end, outing.mode)


def replan(outing):
    """Replace the outing's stops with a freshly planned route."""
    participants = list(outing.participants.all())
    route = outings.plan(
        (float(outing.start_lat), float(outing.start_lng)),
        (float(outing.end_lat), float(outing.end_lng)),
        outing.mode,
        outing.duration_minutes,
        outings.candidates(outing.team, participants, outing.city),
    )
    set_stops(outing, route)


def set_stops(outing, invaders):
    outing.stops.all().delete()
    OutingStop.objects.bulk_create(
        OutingStop(outing=outing, invader=invader, position=index) for index, invader in enumerate(invaders, start=1)
    )


class OutingViewSet(viewsets.ModelViewSet):
    """Team outings. Any member may edit one; only its author or a team admin may delete it."""

    serializer_class = OutingSerializer

    def get_queryset(self):
        team = self.request.user.team
        # How many of the outing's participants flashed each stop's invader.
        participant_flashes = (
            Flash.objects.filter(invader=OuterRef("invader"), user__outings=OuterRef("outing"))
            .values("invader")
            .annotate(count=Count("pk"))
            .values("count")
        )
        stops = OutingStop.objects.select_related("invader").annotate(
            participant_flashes=Coalesce(Subquery(participant_flashes, output_field=IntegerField()), Value(0))
        )
        return (
            Outing.objects.filter(team=team)
            .select_related("created_by")
            .prefetch_related("participants", Prefetch("stops", queryset=stops))
        )

    def get_throttles(self):
        # Planning walks through every candidate invader: a dedicated, tighter rate.
        if self.action in ("create", "plan", "optimize"):
            self.throttle_scope = "outing_plan"
        return super().get_throttles()

    def perform_create(self, serializer):
        # Not a model field: set the stops once the outing exists.
        stop_ids = serializer.validated_data.pop("stop_ids", None)
        with transaction.atomic():
            outing = serializer.save(team=self.request.user.team, created_by=self.request.user)
            if stop_ids is None:
                replan(outing)
            else:
                set_stops(outing, stop_ids)
        # Answer with the annotated stops (done flags), like a GET.
        serializer.instance = self.get_queryset().get(pk=outing.pk)

    def perform_update(self, serializer):
        stop_ids = serializer.validated_data.pop("stop_ids", None)
        with transaction.atomic():
            outing = serializer.save()
            if stop_ids is not None:
                set_stops(outing, stop_ids)
        serializer.instance = self.get_queryset().get(pk=outing.pk)

    def perform_destroy(self, outing):
        user = self.request.user
        if outing.created_by_id != user.pk and not user.is_team_admin:
            raise PermissionDenied("Seul l'auteur de la sortie ou un administrateur peut la supprimer.")
        outing.delete()

    def _fresh(self, outing):
        return Response(self.get_serializer(self.get_queryset().get(pk=outing.pk)).data)

    @action(detail=True, methods=["post"])
    def plan(self, request, pk=None):
        """Recompute the whole route from the outing's settings."""
        outing = self.get_object()
        with transaction.atomic():
            replan(outing)
        return self._fresh(outing)

    @action(detail=True, methods=["post"])
    def optimize(self, request, pk=None):
        """Shortest order for the current invaders (same invaders, new order)."""
        outing = self.get_object()
        invaders = [stop.invader for stop in outing.stops.all()]
        start = (float(outing.start_lat), float(outing.start_lng))
        end = (float(outing.end_lat), float(outing.end_lng))
        with transaction.atomic():
            set_stops(outing, outings.improve_order(start, invaders, end, outing.mode))
        return self._fresh(outing)

