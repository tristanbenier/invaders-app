from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from .images import normalize_image
from .models import City, Country, Flash, Invader, InvaderHistory
from .naming import PREFIX_PATTERN, parse_name

MAX_IMAGE_SIZE = 10 * 1024 * 1024


class NormalizedImageField(serializers.ImageField):
    """Image upload, resized and re-encoded as JPEG. null clears the image."""

    def __init__(self, **kwargs):
        kwargs.setdefault("required", False)
        kwargs.setdefault("allow_null", True)
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        if data.size > MAX_IMAGE_SIZE:
            raise serializers.ValidationError("L'image dépasse la taille maximale de 10 Mo.")
        return normalize_image(super().to_internal_value(data))

    def validate_empty_values(self, data):
        is_empty, value = super().validate_empty_values(data)
        # Image fields are not nullable: an empty string means "no image".
        return (is_empty, "" if is_empty and value is None else value)


class TeamScopedPrimaryKeyField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        return self.queryset.filter(team=self.context["team"])


class UserSummarySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    display_name = serializers.CharField()


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ["id", "name"]

    def validate_name(self, name):
        name = name.strip()
        duplicates = Country.objects.filter(team=self.context["team"], name__iexact=name)
        if self.instance is not None:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise serializers.ValidationError("Ce pays existe déjà.")
        return name


class CitySerializer(serializers.ModelSerializer):
    country = TeamScopedPrimaryKeyField(queryset=Country.objects.all(), required=False)
    # Alternative to country: creates the country on the fly if it does not exist.
    country_name = serializers.CharField(max_length=100, write_only=True, required=False)
    image = NormalizedImageField()

    class Meta:
        model = City
        fields = ["id", "name", "prefix", "country", "country_name", "image"]

    def validate_name(self, name):
        return name.strip()

    def validate_prefix(self, prefix):
        prefix = prefix.strip().upper()
        if self.instance is not None and prefix != self.instance.prefix:
            raise serializers.ValidationError("Le préfixe d'une ville ne peut pas être modifié.")
        if not PREFIX_PATTERN.match(prefix):
            raise serializers.ValidationError("Le préfixe ne doit contenir que des lettres, par exemple PA.")
        duplicates = City.objects.filter(team=self.context["team"], prefix=prefix)
        if self.instance is not None:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise serializers.ValidationError("Une ville utilise déjà ce préfixe.")
        return prefix

    def validate_country_name(self, country_name):
        return country_name.strip()

    def validate(self, attrs):
        if "country" in attrs and attrs.get("country_name"):
            raise serializers.ValidationError("Indiquez soit un pays existant, soit le nom d'un nouveau pays.")
        if self.instance is None and "country" not in attrs and not attrs.get("country_name"):
            raise serializers.ValidationError({"country": ["Ce champ est obligatoire."]})
        return attrs

    def _resolve_country(self, validated_data):
        if country_name := validated_data.pop("country_name", ""):
            team = self.context["team"]
            validated_data["country"] = (
                Country.objects.filter(team=team, name__iexact=country_name).first()
                or Country.objects.create(team=team, name=country_name)
            )
        return validated_data

    @transaction.atomic
    def create(self, validated_data):
        return super().create(self._resolve_country(validated_data))

    @transaction.atomic
    def update(self, instance, validated_data):
        return super().update(instance, self._resolve_country(validated_data))


class InvaderSerializer(serializers.ModelSerializer):
    lat = serializers.FloatField(min_value=-90, max_value=90)
    lng = serializers.FloatField(min_value=-180, max_value=180)
    image = NormalizedImageField()
    created_by = UserSummarySerializer(read_only=True)
    # Annotated by InvaderViewSet.get_queryset().
    my_flashed_at = serializers.DateField(read_only=True, default=None)
    flash_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Invader
        fields = [
            "id",
            "name",
            "city",
            "lat",
            "lng",
            "points",
            "status",
            "image",
            "address1",
            "address2",
            "zip",
            "comment",
            "created_by",
            "created_at",
            "updated_at",
            "my_flashed_at",
            "flash_count",
        ]
        read_only_fields = ["city"]

    def validate_name(self, name):
        name = name.strip().upper()
        if parse_name(name) is None:
            raise serializers.ValidationError("Le nom doit avoir la forme PREFIXE_NUMERO, par exemple PA_123.")
        if self.context.get("check_unique", True):
            duplicates = Invader.objects.filter(team=self.context["team"], name=name)
            if self.instance is not None:
                duplicates = duplicates.exclude(pk=self.instance.pk)
            if duplicates.exists():
                raise serializers.ValidationError("Un invader portant ce nom existe déjà dans l'équipe.")
        return name

    def validate_address1(self, value):
        return value.strip()

    def validate_address2(self, value):
        return value.strip()

    def validate_zip(self, value):
        return value.strip()

    def validate_comment(self, value):
        return value.strip()

    def validate_lat(self, lat):
        return round(lat, 6)

    def validate_lng(self, lng):
        return round(lng, 6)

    def validate(self, attrs):
        if "name" in attrs:
            prefix, _ = parse_name(attrs["name"])
            # The importer passes every team city to avoid one query per row.
            if (cities := self.context.get("cities_by_prefix")) is not None:
                city = cities.get(prefix)
            else:
                city = City.objects.filter(team=self.context["team"], prefix=prefix).first()
            if city is None:
                raise serializers.ValidationError(
                    {"city": [serializers.ErrorDetail(f"Aucune ville ne correspond au préfixe {prefix}.", code="unknown_city")]}
                )
            attrs["city"] = city
        return attrs


class FlasherSerializer(serializers.ModelSerializer):
    user = UserSummarySerializer(read_only=True)

    class Meta:
        model = Flash
        fields = ["user", "flashed_at"]


class InvaderDetailSerializer(InvaderSerializer):
    flashers = serializers.SerializerMethodField()

    class Meta(InvaderSerializer.Meta):
        fields = InvaderSerializer.Meta.fields + ["flashers"]

    def get_flashers(self, invader):
        flashes = invader.flashes.filter(user__is_active=True).select_related("user").order_by("flashed_at")
        return FlasherSerializer(flashes, many=True).data


class FlashInputSerializer(serializers.Serializer):
    flashed_at = serializers.DateField(required=False)

    def validate_flashed_at(self, flashed_at):
        if flashed_at > timezone.localdate():
            raise serializers.ValidationError("La date de flash ne peut pas être dans le futur.")
        return flashed_at


class FlashSerializer(serializers.ModelSerializer):
    invader = InvaderSerializer(read_only=True)

    class Meta:
        model = Flash
        fields = ["id", "invader", "flashed_at"]


class InvaderHistorySerializer(serializers.ModelSerializer):
    user = UserSummarySerializer(read_only=True)

    class Meta:
        model = InvaderHistory
        fields = ["id", "user", "action", "changes", "created_at"]


class ImportOptionsSerializer(serializers.Serializer):
    file = serializers.FileField(required=False)
    mark_as_flashed = serializers.BooleanField(default=False)
