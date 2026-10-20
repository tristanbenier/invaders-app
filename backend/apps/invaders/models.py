from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.functions import Lower

from apps.accounts.models import Team

from .images import UploadTo
from .naming import parse_name


class Country(models.Model):
    team = models.ForeignKey(Team, verbose_name="équipe", related_name="countries", on_delete=models.CASCADE)
    name = models.CharField("nom", max_length=100)

    class Meta:
        verbose_name = "pays"
        verbose_name_plural = "pays"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint("team", Lower("name"), name="unique_country_name_per_team"),
        ]

    def __str__(self):
        return self.name


class City(models.Model):
    team = models.ForeignKey(Team, verbose_name="équipe", related_name="cities", on_delete=models.CASCADE)
    name = models.CharField("nom", max_length=100)
    # Invader name prefix, e.g. "PA" for PA_123. Cannot change once invaders use it.
    prefix = models.CharField("préfixe", max_length=20)
    country = models.ForeignKey(Country, verbose_name="pays", related_name="cities", on_delete=models.PROTECT)
    image = models.ImageField("image", upload_to=UploadTo("cities"), blank=True)

    class Meta:
        verbose_name = "ville"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["team", "prefix"], name="unique_city_prefix_per_team"),
        ]

    def __str__(self):
        return f"{self.name} ({self.prefix})"


class Status(models.TextChoices):
    OK = "ok", "Intact"
    DEGRADED = "degraded", "Dégradé"
    DESTROYED = "destroyed", "Détruit"
    HIDDEN = "hidden", "Caché"
    UNKNOWN = "unknown", "Inconnu"


class Invader(models.Model):
    team = models.ForeignKey(Team, verbose_name="équipe", related_name="invaders", on_delete=models.CASCADE)
    name = models.CharField("nom", max_length=30)
    # Derived from the name, used for natural ordering (PA_2 before PA_10).
    prefix = models.CharField(max_length=20, editable=False)
    number = models.PositiveIntegerField(editable=False)
    # Always the team's city whose prefix matches the name.
    city = models.ForeignKey(City, verbose_name="ville", related_name="invaders", on_delete=models.PROTECT)
    lat = models.DecimalField(
        "latitude", max_digits=9, decimal_places=6, validators=[MinValueValidator(-90), MaxValueValidator(90)]
    )
    lng = models.DecimalField(
        "longitude", max_digits=9, decimal_places=6, validators=[MinValueValidator(-180), MaxValueValidator(180)]
    )
    points = models.PositiveIntegerField("points")
    status = models.CharField("statut", max_length=10, choices=Status.choices, default=Status.OK)
    image = models.ImageField("image", upload_to=UploadTo("invaders"), blank=True)
    address1 = models.CharField("adresse", max_length=255, blank=True)
    address2 = models.CharField("complément d'adresse", max_length=255, blank=True)
    zip = models.CharField("code postal", max_length=20, blank=True)
    comment = models.TextField("commentaire", blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="ajouté par",
        related_name="created_invaders",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField("ajouté le", auto_now_add=True)
    updated_at = models.DateTimeField("modifié le", auto_now=True)

    class Meta:
        verbose_name = "invader"
        ordering = ["prefix", "number"]
        constraints = [
            models.UniqueConstraint(fields=["team", "name"], name="unique_invader_name_per_team"),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = self.name.upper()
        self.prefix, self.number = parse_name(self.name) or (self.name, 0)
        super().save(*args, **kwargs)


class Flash(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="utilisateur", related_name="flashes", on_delete=models.CASCADE
    )
    invader = models.ForeignKey(Invader, verbose_name="invader", related_name="flashes", on_delete=models.CASCADE)
    flashed_at = models.DateField("flashé le")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "flash"
        ordering = ["-flashed_at", "-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "invader"], name="unique_flash_per_user"),
        ]

    def __str__(self):
        return f"{self.user} — {self.invader}"


class HistoryAction(models.TextChoices):
    CREATED = "created", "Création"
    UPDATED = "updated", "Modification"
    IMPORTED = "imported", "Import"


class InvaderHistory(models.Model):
    """Who changed a shared invader and how: every member can edit, this is the safety net."""

    invader = models.ForeignKey(Invader, verbose_name="invader", related_name="history", on_delete=models.CASCADE)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="auteur",
        related_name="invader_changes",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    action = models.CharField("action", max_length=10, choices=HistoryAction.choices)
    # {field: {"old": value, "new": value}}; empty for a creation.
    changes = models.JSONField("modifications", default=dict, blank=True)
    created_at = models.DateTimeField("date", auto_now_add=True)

    class Meta:
        verbose_name = "historique"
        verbose_name_plural = "historique"
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        return f"{self.invader} — {self.get_action_display()}"
