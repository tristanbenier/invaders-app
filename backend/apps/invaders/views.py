from django.db.models import Count, Exists, IntegerField, OuterRef, ProtectedError, Q, Subquery, Value
from django.db.models.functions import Coalesce
from django.http import FileResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.http import require_GET
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsTeamAdmin, IsTeamMember

from . import geocoding, history, importer, tiles
from .models import City, Country, Flash, HistoryAction, Invader, InvaderHistory, Status
from .naming import search_terms
from .serializers import (
    CitySerializer,
    CountrySerializer,
    FlashInputSerializer,
    FlashSerializer,
    ImportOptionsSerializer,
    InvaderDetailSerializer,
    InvaderHistorySerializer,
    InvaderSerializer,
)

ORDERING = {
    "name": ["prefix", "number"],
    "-name": ["-prefix", "-number"],
    "city": ["city__name", "prefix", "number"],
    "-city": ["-city__name", "prefix", "number"],
    "points": ["points", "prefix", "number"],
    "-points": ["-points", "prefix", "number"],
    "created_at": ["created_at"],
    "-created_at": ["-created_at"],
}


class OptionalPagination(PageNumberPagination):
    """Paginate only when ?page is given: the map needs every invader at once."""

    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200

    def paginate_queryset(self, queryset, request, view=None):
        if self.page_query_param not in request.query_params:
            return None
        return super().paginate_queryset(queryset, request, view)


def _id_param(request, param, allow_me=False):
    value = request.query_params.get(param)
    if value is None:
        return None
    if allow_me and value == "me":
        return request.user.pk
    if not value.isdigit():
        raise ValidationError({param: "Identifiant invalide."})
    return int(value)


class TeamScopedViewSet(viewsets.ModelViewSet):
    """CRUD on a model with a team FK; deletion is reserved to team admins."""

    protected_message = "Cet élément est encore utilisé."

    def get_permissions(self):
        if self.action == "destroy":
            return [IsTeamAdmin()]
        return [IsTeamMember()]

    def get_serializer_context(self):
        return {**super().get_serializer_context(), "team": self.request.user.team}

    def get_queryset(self):
        return self.queryset.filter(team=self.request.user.team)

    def perform_create(self, serializer):
        serializer.save(team=self.request.user.team)

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError:
            raise ValidationError(self.protected_message)


class CountryViewSet(TeamScopedViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    protected_message = "Ce pays contient encore des villes."


class CityViewSet(TeamScopedViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    protected_message = "Cette ville contient encore des invaders."


class InvaderViewSet(TeamScopedViewSet):
    pagination_class = OptionalPagination

    def get_serializer_class(self):
        if self.action in ("retrieve", "flash"):
            return InvaderDetailSerializer
        return InvaderSerializer

    def get_queryset(self):
        user = self.request.user
        my_flash = Flash.objects.filter(invader=OuterRef("pk"), user=user)
        flash_count = (
            Flash.objects.filter(invader=OuterRef("pk"), user__is_active=True)
            .values("invader")
            .annotate(count=Count("pk"))
            .values("count")
        )
        queryset = (
            Invader.objects.filter(team=user.team)
            .select_related("created_by")
            .annotate(
                my_flashed_at=Subquery(my_flash.values("flashed_at")[:1]),
                flash_count=Coalesce(Subquery(flash_count, output_field=IntegerField()), Value(0)),
            )
        )
        if self.action == "list":
            queryset = self.filter_queryset_by_params(queryset)
        return queryset

    def filter_queryset_by_params(self, queryset):
        params = self.request.query_params

        if search := params.get("search", "").strip():
            text, exact = search_terms(search)
            matches = Q(name__icontains=text)
            if exact:
                matches |= Q(prefix=exact[0], number=exact[1])
            queryset = queryset.filter(matches)
        if (city := _id_param(self.request, "city")) is not None:
            queryset = queryset.filter(city_id=city)
        if (country := _id_param(self.request, "country")) is not None:
            queryset = queryset.filter(city__country_id=country)
        if statuses := params.get("status"):
            statuses = [value for value in statuses.split(",") if value]
            if invalid := set(statuses) - set(Status.values):
                raise ValidationError({"status": f"Statut inconnu : {', '.join(sorted(invalid))}."})
            queryset = queryset.filter(status__in=statuses)

        flashed = params.get("flashed")
        if flashed in ("true", "false"):
            queryset = queryset.filter(my_flashed_at__isnull=flashed == "false")
        if (member := _id_param(self.request, "flashed_by", allow_me=True)) is not None:
            queryset = queryset.filter(Exists(Flash.objects.filter(invader=OuterRef("pk"), user_id=member)))
        if (member := _id_param(self.request, "not_flashed_by", allow_me=True)) is not None:
            queryset = queryset.filter(~Exists(Flash.objects.filter(invader=OuterRef("pk"), user_id=member)))

        ordering = params.get("ordering", "name")
        if ordering not in ORDERING:
            raise ValidationError({"ordering": f"Tri inconnu. Valeurs possibles : {', '.join(ORDERING)}."})
        return queryset.order_by(*ORDERING[ordering])

    def perform_create(self, serializer):
        invader = serializer.save(team=self.request.user.team, created_by=self.request.user)
        history.record(invader, self.request.user, HistoryAction.CREATED)

    def perform_update(self, serializer):
        before = history.snapshot(serializer.instance)
        invader = serializer.save()
        history.record(invader, self.request.user, HistoryAction.UPDATED, before)

    @action(detail=True, methods=["get"], url_path="history")
    def history(self, request, pk=None):
        entries = InvaderHistory.objects.filter(invader=self.get_object()).select_related("user")
        return Response(InvaderHistorySerializer(entries, many=True).data)

    @action(detail=True, methods=["post", "delete"])
    def flash(self, request, pk=None):
        invader = self.get_object()
        if request.method == "DELETE":
            Flash.objects.filter(user=request.user, invader=invader).delete()
        else:
            serializer = FlashInputSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            flashed_at = serializer.validated_data.get("flashed_at", timezone.localdate())
            Flash.objects.update_or_create(user=request.user, invader=invader, defaults={"flashed_at": flashed_at})
        invader = self.get_object()
        return Response(self.get_serializer(invader).data)


class ReverseGeocodeView(APIView):
    """Address of a point (?lat=&lng=), used to prefill the invader form."""

    throttle_scope = "geocode"

    def get(self, request):
        try:
            lat = float(request.query_params["lat"])
            lng = float(request.query_params["lng"])
        except (KeyError, ValueError):
            raise ValidationError("Les paramètres lat et lng sont obligatoires.")
        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            raise ValidationError("Coordonnées invalides.")
        try:
            return Response(geocoding.reverse(lat, lng))
        except geocoding.GeocodingError:
            return Response(
                {"detail": "Impossible de trouver l'adresse pour le moment."}, status=status.HTTP_502_BAD_GATEWAY
            )


class AddressSearchView(APIView):
    """Places matching ?q= (optionally biased by ?lat=&lng=), for the map search box."""

    throttle_scope = "geocode"

    def get(self, request):
        text = request.query_params.get("q", "").strip()
        if len(text) < 3:
            raise ValidationError("Saisissez au moins 3 caractères.")
        near = None
        try:
            if "lat" in request.query_params and "lng" in request.query_params:
                near = (float(request.query_params["lat"]), float(request.query_params["lng"]))
        except ValueError:
            raise ValidationError("Coordonnées invalides.")
        try:
            return Response(geocoding.search(text[:200], near))
        except geocoding.GeocodingError:
            return Response(
                {"detail": "La recherche d'adresse est indisponible pour le moment."}, status=status.HTTP_502_BAD_GATEWAY
            )


class MyFlashListView(generics.ListAPIView):
    serializer_class = FlashSerializer
    pagination_class = OptionalPagination

    def get_queryset(self):
        return Flash.objects.filter(user=self.request.user).select_related("invader", "invader__created_by")


class ImportView(APIView):
    """POST a JSON file (multipart "file") or a JSON list as the request body."""

    parser_classes = [MultiPartParser, FormParser, JSONParser]
    commit = False

    def post(self, request):
        team = request.user.team
        try:
            if isinstance(request.data, list):
                rows = importer.validate_rows_shape(request.data)
                mark_as_flashed = request.query_params.get("mark_as_flashed") == "true"
            else:
                options = ImportOptionsSerializer(data=request.data)
                options.is_valid(raise_exception=True)
                if "file" not in options.validated_data:
                    raise ValidationError({"file": "Aucun fichier fourni."})
                rows = importer.read_rows(options.validated_data["file"])
                mark_as_flashed = options.validated_data["mark_as_flashed"]
        except importer.ImportFileError as exc:
            raise ValidationError({"file": str(exc)})

        result = importer.analyze(team, rows)
        summary = importer.summarize(result)
        if not self.commit:
            return Response(summary)
        if result["errors"]:
            return Response(summary, status=status.HTTP_400_BAD_REQUEST)
        return Response(importer.commit(team, request.user, result, mark_as_flashed), status=status.HTTP_201_CREATED)


@require_GET
def map_tile(request, z, x, y):
    """OSM tile relayed through the server (see tiles.py). Members only: not an open proxy."""
    user = request.user
    if not (user.is_authenticated and user.team_id):
        return HttpResponse(status=403)
    if not tiles.is_valid(z, x, y):
        return HttpResponse(status=404)
    try:
        try:
            tile = tiles.get_tile(z, x, y).open("rb")
        except FileNotFoundError:
            # Deleted by a concurrent pruning pass between the check and the read.
            tile = tiles.get_tile(z, x, y).open("rb")
    except tiles.TileError:
        return HttpResponse(status=502)
    tiles.maybe_prune_async()
    response = FileResponse(tile, content_type="image/png")
    # Let the browser keep tiles for a day instead of asking again on every reload.
    response["Cache-Control"] = "private, max-age=86400"
    return response
